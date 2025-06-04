"""
Entrypoint.
"""
from loguru import logger
from config import settings       
from tradebot.application.parser import BasicSignalParser
from tradebot.application.order_generator import SimpleOrderGenerator
from tradebot.application.risk import FiboRiskManager
from tradebot.infrastructure.mt5_engine import MetaTraderEngine
from tradebot.infrastructure.telegram_listener import TelegramSignalListener

def bootstrap():

    logger.add("tradebot.log", rotation="25 MB", level="DEBUG")

    parser           = BasicSignalParser()
    engine           = MetaTraderEngine()
    risk_manager     = FiboRiskManager(reverse=True)
    order_generator  = SimpleOrderGenerator(risk_manager=risk_manager)

    gateway          = TelegramSignalListener(
        parser,
        engine,
        order_generator,
    )
    gateway.run()

if __name__ == "__main__":
    bootstrap()
