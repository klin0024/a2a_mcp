from abc import ABC, abstractmethod
from typing import TypedDict


class AgentToolResult(TypedDict):
    ai_message: str
    thread_id: str


class BaseAgentToolService(ABC):
    """Shared contract for anything registered as an agent_tool MCP tool.

    Concrete subclasses (ADKAgentToolService, A2AAgentToolService, ...) differ
    only in how they reach the agent (local ADK Runner vs. a remote A2A
    endpoint). server.py registers instances directly as FastMCP tools:
    `self.__doc__` becomes the tool's description, and `__call__`'s own
    docstring's "Args:" section is parsed by FastMCP into per-parameter
    descriptions on the tool's inputSchema.
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """對外註冊的 MCP tool 名稱。"""

    @abstractmethod
    async def __call__(self, user_message: str, thread_id: str | None = None) -> AgentToolResult:
        """呼叫 agent 並取得回覆。

        Args:
            user_message: 傳送給 agent 的提問。
            thread_id: None 表示開啟新對話；帶入既有值則接續該對話的上下文。
        """
