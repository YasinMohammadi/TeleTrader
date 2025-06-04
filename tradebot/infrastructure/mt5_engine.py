# tradebot\infrastructure\mt5_engine.py

import MetaTrader5 as mt5
from loguru import logger
from tradebot.domain.models import Order, OrderResult
from tradebot.domain.ports import TradingEnginePort
from ._mt5_symbol_resolver import SymbolResolver
from ._magic import MagicGen
from config import settings

from ._mt5_utils import ensure_mt5

class MetaTraderEngine(TradingEnginePort):
    def __init__(self):
        ensure_mt5()
        self._resolver = SymbolResolver()

    # ------------------
    def execute_order(self, order: Order) -> OrderResult: 
                
        symbol_mt = self._resolver.resolve(order.symbol)                            
        if not mt5.symbol_select(symbol_mt, True):
            return OrderResult(False, f"cannot select {symbol_mt}")
        
        # ----- lot size from risk pct -----
        volume = self._calc_volume(order)
        if volume <= 0:
            return OrderResult(False, "volume calc returned 0")

        # ------ choose action + mt5_type + price ------
        bid, ask = self._current_prices(symbol_mt)

        if order.order_type == "limit":
            action = mt5.TRADE_ACTION_PENDING

            if order.side == "buy":
                if order.price is not None and order.price <= ask:
                    mt5_type = mt5.ORDER_TYPE_BUY_LIMIT
                else:
                    mt5_type = mt5.ORDER_TYPE_BUY_STOP
            else:
                # sell side
                if order.price is not None and order.price >= bid:
                    mt5_type = mt5.ORDER_TYPE_SELL_LIMIT
                else:
                    mt5_type = mt5.ORDER_TYPE_SELL_STOP

            price = order.price
            if price is None:
                price = ask if order.side == "buy" else bid

        else:
            
            action  = mt5.TRADE_ACTION_DEAL
            if order.side == "buy":
                mt5_type = mt5.ORDER_TYPE_BUY
                price    = ask
            else:
                mt5_type = mt5.ORDER_TYPE_SELL
                price    = bid

        request = dict(
            action     = action,
            symbol     = symbol_mt,
            volume     = volume,
            type       = mt5_type,
            price      = price,
            sl         = order.sl or 0,
            tp         = order.tp or 0,
            deviation  = settings.max_slippage,
            magic      = MagicGen.generate(),
            comment    = order.comment[:30],      
            type_time  = mt5.ORDER_TIME_GTC,
            # type_filling = mt5.ORDER_FILLING_RETURN,
        )
        logger.debug(f"Sending MT5 request: {request}") 
        
        res = mt5.order_send(request)
        data = res._asdict() if res and hasattr(res, "_asdict") else None

        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Order sent OK — ticket {res.order}")
            return OrderResult(True, "executed", data=data)

        logger.error(f"Order failed: {data} | last_error: {mt5.last_error()}")
        return OrderResult(False, "mt5 error", data=data)
    # ------------------
    def _current_order_price(self, order: Order) -> float:
        """
        Returns bid or ask in respect to order 
        """
        symbol_mt = self._resolver.resolve(order.symbol)
        tick = mt5.symbol_info_tick(symbol_mt)
        if not tick:
            raise RuntimeError(f"No tick for {symbol_mt}")
        return tick.ask if order.side == "buy" else tick.bid
    
    def _current_prices(self, symbol_mt: str) -> tuple[float, float]:
        """
        Returns (bid, ask) price
        """
        tick = mt5.symbol_info_tick(symbol_mt)
        if not tick:
            raise RuntimeError(f"No tick for {symbol_mt}")
        return tick.bid, tick.ask
    
    # ------------------------------------------------------------------    
    def _calc_volume(self, order: Order) -> float:
        """
        Convert risk (percent of balance) into lots.
        volume = (risk_money) / (monetary_value_per_point * stop_distance_points)
        """

        symbol_mt = self._resolver.resolve(order.symbol)
        acc = mt5.account_info()
        balance = acc.balance if acc else 0
        if balance == 0:
            return 0

        sym_info = mt5.symbol_info(symbol_mt)
        if sym_info is None:
            return 0

        money_per_point = (sym_info.trade_tick_value / sym_info.trade_tick_size) * sym_info.point

        # Stop distance in points
        if order.sl:
            stop_distance = abs((order.price or self._current_order_price(order)) - order.sl) / sym_info.point
        else:
            stop_distance = 0  

        if stop_distance == 0:
            return 0

        risk_money   = balance * order.risk
        raw_volume   = risk_money / (money_per_point * stop_distance)

        # round to volume_step & 2 decimals
        step   = sym_info.volume_step
        round_volume = round(raw_volume / step) * step
        volume = max(round_volume, sym_info.volume_min)
        logger.debug(f"For the Risk {round_volume} we should {order.side} {volume} lots!")
        return round(volume, 2)

