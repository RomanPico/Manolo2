"""Application settings loaded from environment."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_path: str = Field(default="data/manolo.sqlite3", alias="DATABASE_PATH")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    llama_cpp_base_url: str = Field(default="http://127.0.0.1:8080/v1", alias="LLAMA_CPP_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    fx_api_url: str = Field(
        default="https://open.er-api.com/v6/latest/USD",
        alias="FX_API_URL",
    )

    max_steps: int = Field(default=10, alias="MAX_STEPS")
    max_tool_calls: int = Field(default=10, alias="MAX_TOOL_CALLS")
    allowed_tools: str = Field(
        default="calendar_tool,usd_price_tool",
        alias="ALLOWED_TOOLS",
    )

    def allowed_tools_list(self) -> list[str]:
        """Return allowed tool names as a list."""
        return [t.strip() for t in self.allowed_tools.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
