import MetaTrader5 as mt5
from loguru import logger
from tradebot.domain.models import Order, OrderResult
from tradebot.domain.ports import TradingEnginePort
from config import settings

class MetaTraderEngine(TradingEnginePort):
    def __init__(self):
        if not mt5.initialize(settings.mt5_path):
            logger.info("Couldn't Initailize MT5 Terminal")
            mt5.shutdown()
            raise RuntimeError(mt5.last_error())
        if not mt5.login(settings.mt_account,
                         password=settings.mt_password,
                         server=settings.mt_server):
            raise RuntimeError(mt5.last_error())
        logger.info("MT5 logged in OK.")

    # ------------------
    def execute_order(self, order: Order) -> OrderResult: 
                
        symbol_mt = f"{order.symbol}b"                             
        if not mt5.symbol_select(symbol_mt, True):
            return OrderResult(False, f"cannot select {symbol_mt}")

        mt5_type = (mt5.ORDER_TYPE_BUY if order.side == "buy"
                    else mt5.ORDER_TYPE_SELL)

        price = order.price or self._current_price(order)
        new_order = dict(
            action     = mt5.TRADE_ACTION_DEAL,
            symbol     = symbol_mt,
            volume     = order.volume,
            type       = mt5_type,
            price      = price,
            sl         = order.sl or 0,
            tp         = order.tp or 0,
            deviation  = settings.max_slippage,
            magic      = settings.magic_number,
            comment    = order.comment[:30],      
            type_time  = mt5.ORDER_TIME_GTC,
            # type_filling = mt5.ORDER_FILLING_RETURN,
        )
        logger.debug(f"Trying to Execute: {new_order}") 

        request = dict(
            action     = mt5.TRADE_ACTION_DEAL,
            symbol     = symbol_mt,
            volume     = order.volume,
            type       = mt5_type,
            price      = price,
            sl         = order.sl or 0,
            tp         = order.tp or 0,
            deviation  = settings.max_slippage,
            magic      = settings.magic_number,
            comment    = order.comment[:30],      # MT5 comment limit
            type_time  = mt5.ORDER_TIME_GTC,
            # type_filling = mt5.ORDER_FILLING_RETURN,
        )

        res = mt5.order_send(request)
        data = res._asdict() if res and hasattr(res, "_asdict") else None

        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info("Order sent OK — ticket %s", res.order)
            return OrderResult(True, "executed", data=data)

        logger.error(f"Order failed: {data} | last_error: {mt5.last_error()}")
        return OrderResult(False, "mt5 error", data=data)
    # ------------------
    def _current_price(self, order: Order) -> float:
        symbol_mt = f"{order.symbol}b"
        tick = mt5.symbol_info_tick(symbol_mt)
        if not tick:
            raise RuntimeError(f"No tick for {symbol_mt}")
        return tick.ask if order.side == "buy" else tick.bid
