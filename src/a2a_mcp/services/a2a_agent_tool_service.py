import uuid
from dataclasses import dataclass

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.client.helpers import create_text_message_object
from a2a.types import AgentCard, AgentSkill, Message, Part, TextPart
from pydantic import ValidationError

from a2a_mcp.services.base import AgentToolResult, BaseAgentToolService


@dataclass
class A2AAgentToolServiceConfig:
    agent_card_path: str  # 本機 agent card JSON 檔案路徑
    agent_name: str | None = None  # None -> 用 agent_card.name
    timeout: float = 30.0  # httpx timeout（秒）；預設的 5 秒對一般 LLM 回應時間太短


def _extract_text(parts: list[Part]) -> str:
    texts = [p.root.text for p in parts if isinstance(p.root, TextPart)]
    return "\n".join(t for t in texts if t)


def _format_skills(skills: list[AgentSkill]) -> str:
    lines = []
    for skill in skills:
        line = f"- {skill.name}: {skill.description}"
        if skill.examples:
            line += "\n  範例：" + " / ".join(skill.examples)
        lines.append(line)
    return "\n".join(lines)


class A2AAgentToolService(BaseAgentToolService):
    """Wraps a remote A2A agent behind the agent_tool contract.

    agent card 是本機檔案（不透過 HTTP 動態解析），所以 client 建立是同步的，
    可以直接放在 __init__ 裡做。

    thread_id *is* the A2A context_id, used as-is (no encoding/prefix).
    Conversation state lives entirely on the remote A2A agent, keyed by its
    own context_id — there is no local session store to manage here (unlike
    ADKAgentToolService, which owns an ADK SessionService).
    """

    def __init__(self, config: A2AAgentToolServiceConfig):
        self.agent_card_path = config.agent_card_path
        self.agent_card = self._load_agent_card(config.agent_card_path)
        self.agent_name = config.agent_name or self.agent_card.name

        # streaming=True 對 adk api_server --a2a 曝露的 agent 會 timeout，改用非串流呼叫
        httpx_client = httpx.AsyncClient(timeout=config.timeout)
        client_config = ClientConfig(streaming=False, httpx_client=httpx_client)
        self._client = ClientFactory(client_config).create(self.agent_card)

        summary = self.agent_card.description or f"呼叫遠端 A2A agent「{self.agent_name}」進行對話。"
        doc_parts = [summary]
        skills_text = _format_skills(self.agent_card.skills)
        if skills_text:
            doc_parts.append(f"Skills:\n{skills_text}")
        doc_parts.append(
            "首次呼叫不帶 thread_id 開始新對話；"
            "之後帶入上次回傳的 thread_id 即可延續同一段對話的上下文。"
        )
        self.__doc__ = "\n\n".join(doc_parts)

    @property
    def tool_name(self) -> str:
        """對外註冊的 MCP tool 名稱，與 agent_name 一致。"""
        return self.agent_name

    async def __call__(self, user_message: str, thread_id: str | None = None) -> AgentToolResult:
        """呼叫遠端 A2A agent 並取得回覆。

        Args:
            user_message: 傳送給 agent 的提問。
            thread_id: None 表示開啟新對話；帶入既有值則接續該對話的上下文。
        """
        if not user_message:
            raise ValueError("user_message must not be empty")

        context_id = thread_id

        message = create_text_message_object(content=user_message)
        if context_id is not None:
            message.context_id = context_id

        ai_message = ""
        response_context_id = context_id
        async for event in self._client.send_message(message):
            if isinstance(event, Message):
                text = _extract_text(event.parts)
                if text:
                    ai_message = text
                if event.context_id:
                    response_context_id = event.context_id
            else:
                # event 是 (Task, update_event | None)
                task, _update_event = event
                if task.context_id:
                    response_context_id = task.context_id
                for artifact in task.artifacts or []:
                    text = _extract_text(artifact.parts)
                    if text:
                        ai_message = text

        if not ai_message:
            raise RuntimeError("remote A2A agent did not produce a text response")
        if response_context_id is None:
            # 遠端沒回傳 context_id，退而求其次自己生一個（下次帶回去遠端不一定認得）
            response_context_id = str(uuid.uuid4())

        return {"ai_message": ai_message, "thread_id": response_context_id}

    # -- agent card 載入 --

    @staticmethod
    def _load_agent_card(path: str) -> AgentCard:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        try:
            return AgentCard.model_validate_json(text)
        except ValidationError as e:
            # 涵蓋 JSON 格式錯誤與缺必要欄位兩種情況；補上檔案路徑，不然看不出是哪個檔案壞掉
            raise ValueError(f"invalid agent card at {path!r}: {e}") from e
