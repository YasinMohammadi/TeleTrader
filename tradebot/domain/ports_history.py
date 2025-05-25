# tradebot/domain/ports_history.py
from abc import ABC, abstractmethod
import pandas as pd

class TradeHistoryPort(ABC):
    """Fetch executed trades into a tidy DataFrame."""

    @abstractmethod
    def fetch_positiosn(self) -> pd.DataFrame:
        """
        Return a DataFrame with at least:
        ['time', 'symbol', 'side', 'volume', 'price_open',
         'price_close', 'profit', 'comment']
        The index should be UTC DatetimeIndex.
        """
