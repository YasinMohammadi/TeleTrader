"""
Centralised runtime configuration (pydantic v2).
Reads environment variables or .env automatically.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    telegram_token: str      = Field(..., alias="TELEGRAM_TOKEN")
    signal_chat_id: int      = Field(..., alias="SIGNAL_CHAT_ID")

    mt5_path: str            = Field(..., alias="TERMINAL_PATH")
    mt_account: int          = Field(..., alias="MT_ACCOUNT")
    mt_password: str         = Field(..., alias="MT_PASSWORD")
    mt_server: str           = Field(..., alias="BROKER_SERVER")

    risk_per_trade: float    = Field(0.01, ge=0, le=1)
    max_slippage: int        = Field(20)
    magic_number: int        = Field(32001)

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra    = "ignore"
    )

settings = Settings()
