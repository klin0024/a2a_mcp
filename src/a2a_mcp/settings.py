from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# google-adk / google-genai 直接讀 process 環境變數找 GOOGLE_API_KEY，這裡也載入 os.environ
load_dotenv()

AGENTS_DIR = Path(__file__).parent / "agents"
ADK_AGENTS_DIR = AGENTS_DIR / "adk"
A2A_AGENTS_DIR = AGENTS_DIR / "a2a"
LANGCHAIN_AGENTS_DIR = AGENTS_DIR / "langchain"


def discover_adk_agent_names() -> list[str]:
    """掃描 agents/adk/ 目錄，回傳每個含 agent.py 的子目錄名稱。"""
    return sorted(
        p.name
        for p in ADK_AGENTS_DIR.iterdir()
        if p.is_dir() and (p / "agent.py").exists()
    )


def discover_a2a_agent_names() -> list[str]:
    """掃描 agents/a2a/ 目錄，回傳每個含 agent_card.json 的子目錄名稱。"""
    return sorted(
        p.name
        for p in A2A_AGENTS_DIR.iterdir()
        if p.is_dir() and (p / "agent_card.json").exists()
    )


def discover_langchain_agent_names() -> list[str]:
    """掃描 agents/langchain/ 目錄，回傳每個含 agent.py 的子目錄名稱。"""
    return sorted(
        p.name
        for p in LANGCHAIN_AGENTS_DIR.iterdir()
        if p.is_dir() and (p / "agent.py").exists()
    )


def _split_csv(v: object) -> object:
    if isinstance(v, str):
        return [name.strip() for name in v.split(",") if name.strip()]
    return v


class Settings(BaseSettings):
    """集中管理環境變數設定（讀取 .env），取代散落在各處的 os.environ.get(...)。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str | None = None
    log_level: str = "INFO"

    # None -> 自動掃描對應目錄全部 agent；三種後端分開設定，互不影響
    adk_agent_names: list[str] | None = None
    a2a_agent_names: list[str] | None = None
    langchain_agent_names: list[str] | None = None

    @field_validator("adk_agent_names", "a2a_agent_names", "langchain_agent_names", mode="before")
    @classmethod
    def _split_agent_names_csv(cls, v: object) -> object:
        return _split_csv(v)

    def resolve_adk_agent_names(self) -> list[str]:
        if self.adk_agent_names is not None:
            return list(self.adk_agent_names)
        return discover_adk_agent_names()

    def resolve_a2a_agent_names(self) -> list[str]:
        if self.a2a_agent_names is not None:
            return list(self.a2a_agent_names)
        return discover_a2a_agent_names()

    def resolve_langchain_agent_names(self) -> list[str]:
        if self.langchain_agent_names is not None:
            return list(self.langchain_agent_names)
        return discover_langchain_agent_names()


settings = Settings()
