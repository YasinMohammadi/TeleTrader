# tradebot/infrastructure/mt5_history.py
import pandas as pd
import MetaTrader5 as mt5
from loguru import logger
from tradebot.domain.ports_history import TradeHistoryPort
from config import settings

from ._mt5_utils import ensure_mt5

class MT5HistoryRepository(TradeHistoryPort):
    """Pull trade history from the connected MT5 terminal."""

    def __init__(self):
        ensure_mt5()

    def fetch_positiosn(self) -> pd.DataFrame:
        # pull last 365 days (adapt as needed)
        from datetime import datetime, timedelta, timezone
        utc_to = datetime.now(timezone.utc)
        utc_fr = utc_to - timedelta(days=365)

        deals = mt5.history_deals_get(utc_fr, utc_to)
        if deals is None:
            raise RuntimeError("history_deals_get returned None")

        df = pd.DataFrame(list(deals),columns=deals[0]._asdict().keys())
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df.set_index("time", inplace=True)
        return df[
            ["symbol", "type", "volume", "price", "profit", "comment"]
        ].rename(columns={
            "type": "side",
            "price": "price_open"
        })
