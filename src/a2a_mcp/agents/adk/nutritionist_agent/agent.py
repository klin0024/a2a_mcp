"""營養師 Agent（Google ADK 版）。

沿用專案根目錄的 system-prompt.md 與 skills/，Exa 透過 MCP 接入。
執行：在上一層目錄跑 `adk web` 或 `adk run nutritionist_agent`。
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.skill_toolset import SkillDiscoveryMode, SkillToolset

PROJECT_ROOT = Path(__file__).resolve().parent
SKILLS_DIR = PROJECT_ROOT / "skills"

# red-flag-screening 要求「永遠在背景執行」，直接放進 system instruction，
# 不靠模型自己去 load_skill。
ALWAYS_ON_SKILL = "red-flag-screening"

MODEL = os.getenv("NUTRITIONIST_MODEL", "gemini-2.5-flash")


def _build_instruction() -> str:
  system_prompt = (PROJECT_ROOT / "system-prompt.md").read_text(encoding="utf-8")
  red_flag = load_skill_from_dir(SKILLS_DIR / ALWAYS_ON_SKILL)
  return (
      f"{system_prompt}\n\n"
      "## 使用 skills\n\n"
      "system prompt 中提到的 skill（例如 `intake-interview`、`energy-needs-calc`）"
      "都可以用 `load_skill` 工具載入完整說明，進入對應流程前先載入。\n\n"
      f"## 永遠啟用：{ALWAYS_ON_SKILL}\n\n"
      f"{red_flag.instructions}"
  )


def _build_skill_toolset() -> SkillToolset:
  skills = [
      load_skill_from_dir(d)
      for d in sorted(SKILLS_DIR.iterdir())
      if (d / "SKILL.md").is_file() and d.name != ALWAYS_ON_SKILL
  ]
  return SkillToolset(skills=skills, discovery_mode=SkillDiscoveryMode.EAGER)


def _build_exa_toolset() -> McpToolset:
  # Exa 託管的 MCP 不帶 key 也能用（有免費額度限制），所以 key 是選填。
  url = "https://mcp.exa.ai/mcp"
  if api_key := os.getenv("EXA_API_KEY", "").strip():
    url += f"?exaApiKey={api_key}"
  return McpToolset(
      connection_params=StreamableHTTPConnectionParams(url=url, timeout=30),
      tool_filter=["web_search_exa", "web_fetch_exa", "crawling_exa"],
  )


tools = [_build_skill_toolset(), _build_exa_toolset()]

root_agent = LlmAgent(
    name="nutritionist_agent",
    model=MODEL,
    description="以實證為基礎、在地化（台灣）的 AI 營養諮詢助理。",
    instruction=_build_instruction(),
    tools=tools,
)
