import uuid
from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from a2a_mcp.services.base import AgentToolResult, BaseAgentToolService


@dataclass
class LangChainAgentToolServiceConfig:
    build_agent: Callable[[BaseCheckpointSaver], CompiledStateGraph]  # agents/langchain/{name}/agent.py 的 build_agent(checkpointer)
    agent_name: str | None = None  # None -> 用 self.agent.name
    description: str | None = None  # None -> 通用預設句子（CompiledStateGraph 不暴露 system_prompt，反查不到）
    checkpointer: BaseCheckpointSaver | None = None  # None -> 用 InMemorySaver()


class LangChainAgentToolService(BaseAgentToolService):
    """Wraps a langchain.agents.create_agent() graph behind the agent_tool contract.

    checkpointer 比照 ADKAgentToolServiceConfig.session_service，預設 in-memory、可覆蓋。
    agent_name 預設從編譯好的 self.agent.name 讀回；description 沒有等效管道（CompiledStateGraph
    不暴露 system_prompt），沒給就退回通用句子。
    thread_id 是 checkpointer 原生的不透明字串，比照 A2AAgentToolService 的 context_id：
    新對話配一個 uuid4，之後原樣傳回。
    """

    def __init__(self, config: LangChainAgentToolServiceConfig):
        self.checkpointer = config.checkpointer or InMemorySaver()
        self.agent = config.build_agent(self.checkpointer)
        self.agent_name = config.agent_name or self.agent.name

        summary = config.description or f"呼叫 {self.agent_name} agent 進行對話。"
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
            thread_id = str(uuid.uuid4())

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": thread_id}},
        )

        messages = result.get("messages") or []
        last_message = messages[-1] if messages else None
        if not isinstance(last_message, AIMessage) or not last_message.text:
            raise RuntimeError("agent did not produce a final response")

        return {"ai_message": last_message.text, "thread_id": thread_id}
