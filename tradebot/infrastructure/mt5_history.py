import pandas as pd, MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone
from loguru import logger
from ._mt5_utils import ensure_mt5
from tradebot.domain.ports_history import TradeDataPort

class MT5HistoryRepository(TradeDataPort):
    """Fetch both deals & orders once, return tidy DataFrames."""

    def __init__(self):
        ensure_mt5()
        logger.info("MT5 history repository ready")

    # ---------------------------------
    def _pull(self):
        utc_to = datetime.now(timezone.utc)
        utc_fr = utc_to - timedelta(days=365)

        deals  = mt5.history_deals_get (utc_fr, utc_to) or []
        orders = mt5.history_orders_get(utc_fr, utc_to) or []

        df_deals  = pd.DataFrame(d._asdict()  for d in deals)
        df_orders = pd.DataFrame(o._asdict()  for o in orders)

        # Add datetime index for convenience
        if not df_deals.empty:
            df_deals["time"] = pd.to_datetime(df_deals["time"], unit="s", utc=True)
            df_deals.set_index("time", inplace=True)

        if not df_orders.empty:
            df_orders["time_setup"] = pd.to_datetime(df_orders["time_setup"],
                                                     unit="s", utc=True)
            df_orders.set_index("time_setup", inplace=True)

        self._deals, self._orders = df_deals, df_orders

    # ---------------------------------
    def fetch_deals(self) -> pd.DataFrame:
        if not hasattr(self, "_deals"):
            self._pull()
        return self._deals.copy()

    def fetch_orders(self) -> pd.DataFrame:
        if not hasattr(self, "_orders"):
            self._pull()
        return self._orders.copy()
