"""
Lot‑size strategy placeholder.
Extend with account equity, vol calc, ATR etc.
"""
from config import settings
from tradebot.domain.models import Signal

def calc_volume(signal: Signal, price_precision: int = 2) -> float:
    # very naive: fixed lot scaled by risk %
    base_lot = 0.05
    return round(base_lot, price_precision)
