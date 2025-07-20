"""
Centralised runtime configuration (pydantic v2).
Reads environment variables or .env automatically.
"""

from pydantic import Field, BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class MT5Account(BaseModel):
    account: int
    password: str
    server: str
    path: str

class Settings(BaseSettings):
    telegram_token: str      = Field(..., alias="TELEGRAM_TOKEN")
    signal_chat_id: int      = Field(..., alias="SIGNAL_CHAT_ID")

    mt_accounts: List[MT5Account] = []

    risk_per_trade: float    = Field(0.01, ge=0, le=1)
    max_slippage: int        = Field(20)
    magic_number: int        = Field(32001)

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra    = "ignore"
    )

    @model_validator(mode='after')
    def load_mt_accounts(self) -> 'Settings':
        try:
            with open('accounts.json', 'r') as f:
                accounts_data = json.load(f)
            self.mt_accounts = [MT5Account(**acc) for acc in accounts_data]
        except FileNotFoundError:
            # Allow running without accounts file if mt_accounts is already populated
            if not self.mt_accounts:
                raise ValueError("accounts.json not found and MT_ACCOUNTS not in .env")
        except json.JSONDecodeError:
            raise ValueError("Error decoding accounts.json")
        return self

settings = Settings()
