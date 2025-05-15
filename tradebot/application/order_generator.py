# tradebot/application/order_generator.py


from tradebot.domain.models import Signal, Order
from tradebot.application.risk import calc_volume


from tradebot.domain.models import Signal, Order
from tradebot.application.risk import calc_volume

class OrderGenerator:
    """Split a multi‑target Signal into per‑target orders.

    Each target receives an equal fraction of the total risk volume.
    The resulting `Order.comment` is the original comment plus
    a target index, e.g.  "Jasin Trader:Lily T1/3".
    """

    def __init__(self, risk_func=calc_volume):
        self.risk_func = risk_func

    # ------------------------------------------------------------------
    def generate(self, signal: Signal) -> list[Order]:
        total_vol = self.risk_func(signal)
        n_targets = max(len(signal.targets), 1)
        if n_targets == 0:
            return []
        vol_each = round(total_vol / n_targets, 2)

        orders: list[Order] = []
        for idx, tgt in enumerate(signal.targets, start=1):
            tgt_comment = f"{signal.comment} {idx}of{n_targets}".strip()
            orders.append(
                Order(
                    symbol  = signal.symbol,
                    side    = signal.side,
                    volume  = vol_each,
                    price   = signal.entry if signal.order_type == "limit" else None,
                    sl      = signal.stop_loss,
                    tp      = tgt.price,
                    comment = tgt_comment,
                )
            )
        return orders

