import base64
import secrets
from dataclasses import dataclass

from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.genai.types import Content, Part

from a2a_mcp.services.base import AgentToolResult, BaseAgentToolService


@dataclass
class ADKAgentToolServiceConfig:
    agent: BaseAgent  # 已載入好的 ADK agent（例如 agents/adk/{name}/agent.py 的 root_agent）
    agent_name: str | None = None  # None -> 用 agent.name
    app_name: str | None = None  # None -> 用 agent_name 當 app_name
    session_service: BaseSessionService | None = None  # None -> 用 InMemorySessionService()


class ADKAgentToolService(BaseAgentToolService):
    """Wraps a local Google ADK Runner/SessionService behind the agent_tool contract.

    thread_id is a stateless token: base64("USER_ID_{8}:SESSION_ID_{8}").
    All conversation state lives in the ADK SessionService, not here.
    """

    def __init__(self, config: ADKAgentToolServiceConfig):
        self.agent = config.agent
        self.agent_name = config.agent_name or self.agent.name

        self.app_name = config.app_name or self.agent_name
        self.session_service = config.session_service or InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

        summary = self.agent.description or f"呼叫 {self.agent_name} agent 進行對話。"
        self.__doc__ = (
            f"{summary}\n\n"
            "首次呼叫不帶 thread_id 開始新對話；"
            "之後帶入上次回傳的 thread_id 即可延續同一段對話的上下文。"
        )

    @property
    def tool_name(self) -> str:
        """對外註冊的 MCP tool 名稱，與 agent_name 一致。"""
        return self.agent_name

    async def __call__(self, user_message: str, thread_id: str | None = None) -> AgentToolResult:
        """呼叫 agent 並取得回覆。

        Args:
            user_message: 傳送給 agent 的提問。
            thread_id: None 表示開啟新對話；帶入既有值則接續該對話的上下文。
        """
        if not user_message:
            raise ValueError("user_message must not be empty")

        if thread_id is None:
            user_id, session_id = self._generate_ids()
            await self.session_service.create_session(
                app_name=self.app_name, user_id=user_id, session_id=session_id
            )
            thread_id = self._encode(user_id, session_id)
        else:
            user_id, session_id = self._decode(thread_id)
            existing = await self.session_service.get_session(
                app_name=self.app_name, user_id=user_id, session_id=session_id
            )
            if existing is None:
                # session 已不存在 -> 自動重建（沿用同一組 user_id/session_id）
                await self.session_service.create_session(
                    app_name=self.app_name, user_id=user_id, session_id=session_id
                )

        ai_message = await self._run(user_id, session_id, user_message)
        return {"ai_message": ai_message, "thread_id": thread_id}

    # -- id / token 處理 --

    @staticmethod
    def _generate_ids() -> tuple[str, str]:
        # user_id / session_id 本身就帶前綴，直接做為 ADK 的 user_id / session_id 使用
        return f"USER_ID_{secrets.token_hex(4)}", f"SESSION_ID_{secrets.token_hex(4)}"

    @staticmethod
    def _encode(user_id: str, session_id: str) -> str:
        raw = f"{user_id}:{session_id}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    @staticmethod
    def _decode(thread_id: str) -> tuple[str, str]:
        try:
            raw = base64.urlsafe_b64decode(thread_id.encode()).decode()
            user_id, session_id = raw.split(":", 1)
            if not user_id.startswith("USER_ID_") or not session_id.startswith("SESSION_ID_"):
                raise ValueError("missing USER_ID_/SESSION_ID_ prefix")
            return user_id, session_id
        except Exception as e:
            raise ValueError(f"invalid thread_id: {thread_id}") from e

    # -- 執行 agent --

    async def _run(self, user_id: str, session_id: str, user_message: str) -> str:
        content = Content(role="user", parts=[Part(text=user_message)])
        ai_message = None
        async for event in self.runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            if event.is_final_response():
                ai_message = event.content.parts[0].text
        if ai_message is None:
            raise RuntimeError("agent did not produce a final response")
        return ai_message
