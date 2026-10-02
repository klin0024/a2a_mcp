import importlib
import logging

from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from a2a_mcp.services.a2a_agent_tool_service import A2AAgentToolService, A2AAgentToolServiceConfig
from a2a_mcp.services.adk_agent_tool_service import ADKAgentToolService, ADKAgentToolServiceConfig
from a2a_mcp.services.base import BaseAgentToolService
from a2a_mcp.services.langchain_agent_tool_service import LangChainAgentToolService, LangChainAgentToolServiceConfig
from a2a_mcp.settings import A2A_AGENTS_DIR, settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="a2a-mcp")


def register_tool(service: BaseAgentToolService) -> None:
    # description / 各參數說明分別來自 service.__doc__ 與 __call__ 的 docstring
    tool = FunctionTool.from_function(service, name=service.tool_name)
    mcp.add_tool(tool)


def register_adk_agents() -> None:
    for agent_name in settings.resolve_adk_agent_names():
        module_path = f"a2a_mcp.agents.adk.{agent_name}.agent"
        try:
            agent_module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            # 只吞掉「模組不存在」；agent.py 內部自己 import 失敗（e.name 是別的模組）照常往外拋
            if e.name in (module_path, f"a2a_mcp.agents.adk.{agent_name}"):
                logger.warning("ADK_AGENT_NAMES 指定了不存在的 agent %r（找不到 %s），已略過", agent_name, module_path)
                continue
            raise
        config = ADKAgentToolServiceConfig(agent=agent_module.root_agent, agent_name=agent_name)
        register_tool(ADKAgentToolService(config))


def register_a2a_agents() -> None:
    for agent_name in settings.resolve_a2a_agent_names():
        card_path = A2A_AGENTS_DIR / agent_name / "agent_card.json"
        if not card_path.exists():
            logger.warning("A2A_AGENT_NAMES 指定了不存在的 agent %r（找不到 %s），已略過", agent_name, card_path)
            continue
        config = A2AAgentToolServiceConfig(agent_card_path=str(card_path), agent_name=agent_name)
        register_tool(A2AAgentToolService(config))


def register_langchain_agents() -> None:
    for agent_name in settings.resolve_langchain_agent_names():
        module_path = f"a2a_mcp.agents.langchain.{agent_name}.agent"
        try:
            agent_module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            if e.name in (module_path, f"a2a_mcp.agents.langchain.{agent_name}"):
                logger.warning(
                    "LANGCHAIN_AGENT_NAMES 指定了不存在的 agent %r（找不到 %s），已略過", agent_name, module_path
                )
                continue
            raise
        config = LangChainAgentToolServiceConfig(build_agent=agent_module.build_agent, agent_name=agent_name)
        register_tool(LangChainAgentToolService(config))


def register_agents() -> None:
    register_adk_agents()
    register_a2a_agents()
    register_langchain_agents()


register_agents()


if __name__ == "__main__":
    mcp.run()
