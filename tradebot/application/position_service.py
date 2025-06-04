import re, math, pandas as pd, MetaTrader5 as mt5
from tradebot.domain.ports_history import TradeDataPort
from tradebot.domain.models_history import Position

class PositionService:
    """Combine deals+orders → Position objects & simple analytics."""

    _RX = re.compile(r"([A-Za-z]+)\s+(\d+)of(\d+)", re.I)

    def __init__(self, repo: TradeDataPort):
        self.repo = repo

    # -----------------------------------------------------------------
    def positions(self) -> list[Position]:
        deals  = self.repo.fetch_deals()
        orders = self.repo.fetch_orders()

        if deals.empty:
            return []

        pos_list: list[Position] = []

        # quick lookup of SL/TP per position from *opening* order
        ord_first = (orders
                     .sort_index()
                     .drop_duplicates("position_id", keep="first")
                     .set_index("position_id"))
        for pid, g in deals.groupby("position_id"):
            first, last = g.iloc[0], g.iloc[-1]

            # Side
            side_code = int(first["type"]) if "type" in first else int(first["side"])
            side = "buy" if side_code in (0, mt5.ORDER_TYPE_BUY) else "sell"

            # Prices and volume
            vwap = lambda d: (d["price"]*d["volume"]).sum()/d["volume"].sum()
            price_open  = float(vwap(g[g["entry"]==0]) if "entry" in g else vwap(g))
            price_close = float(vwap(g[g["entry"]!=0])) if (g["entry"]!=0).any() else None
            volume      = float(g["volume"].sum())
            profit      = float(g["profit"].sum())
            commiss     = float(g["commission"].sum())

            magic = int(first["magic"]) if not pd.isna(first["magic"]) else None

            # Get SL/TP from first related order if present
            sl = tp = None
            if pid in ord_first.index:
                o = ord_first.loc[pid]
                sl = float(o["sl"]) if o["sl"] else None
                tp = float(o["tp"]) if o["tp"] else None

            rr = None
            if sl and tp and sl != price_open and tp != price_open:
                risk   = abs(price_open - sl)
                reward = abs(tp - price_open)
                rr = round(reward / risk, 2) if risk else None

            # Trader info from first deal comment
            trader, t_idx, t_tot = self._parse_comment(str(first["comment"]))

            pos = Position(
                position_id = int(pid),
                magic       = magic,
                symbol      = str(first["symbol"]),
                side        = side,
                volume      = volume,
                price_open  = price_open,
                price_close = price_close,
                sl          = sl,
                tp          = tp,
                profit      = profit,
                commission  = commiss,
                time_open   = first.name.to_pydatetime(),
                time_close  = last.name.to_pydatetime() if price_close else None,
                duration_sec= int((last.name - first.name).total_seconds()) if price_close else None,
                rr          = rr,
                trader      = trader,
                target_index= t_idx,
                target_total= t_tot,
            )
            pos_list.append(pos)

        return pos_list

    # -----------------------------------------------------------------
    @staticmethod
    def _parse_comment(c: str):
        m = PositionService._RX.search(c)
        if not m:
            return None, None, None
        return m.group(1), int(m.group(2)), int(m.group(3))

    # -----------------------------------------------------------------
    def average_duration(self) -> float:
        """Return mean position duration (seconds) for closed trades."""
        durs = [p.duration_sec for p in self.positions() if p.duration_sec]
        return sum(durs)/len(durs) if durs else 0.0
