import pandas as pd, MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone
from loguru import logger
from ._mt5_utils import ensure_mt5
from tradebot.domain.ports_history import TradeDataPort
from config import settings

class MT5HistoryRepository(TradeDataPort):
    """Fetch both deals & orders once, return tidy DataFrames."""

    def __init__(self):
        ensure_mt5()
        logger.info("MT5 history repository ready")

    # ---------------------------------
    def _pull(self):
        utc_to = datetime.now(timezone.utc)
        utc_fr = utc_to - timedelta(days=365)

        all_deals, all_orders = [], []

        for acc in settings.mt_accounts:
            if not mt5.login(acc.account, acc.password, acc.server):
                logger.warning(f"Login failed for account {acc.account}")
                continue

            logger.info(f"Pulling history for account {acc.account}...")
            deals  = mt5.history_deals_get (utc_fr, utc_to) or []
            orders = mt5.history_orders_get(utc_fr, utc_to) or []

            if deals:
                df_deals = pd.DataFrame(d._asdict() for d in deals)
                df_deals["account_id"] = acc.account
                all_deals.append(df_deals)

            if orders:
                df_orders = pd.DataFrame(o._asdict() for o in orders)
                df_orders["account_id"] = acc.account
                all_orders.append(df_orders)

        df_deals  = pd.concat(all_deals,  ignore_index=True) if all_deals else pd.DataFrame()
        df_orders = pd.concat(all_orders, ignore_index=True) if all_orders else pd.DataFrame()

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
