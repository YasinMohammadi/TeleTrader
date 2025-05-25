"""
Entrypoint.
"""
from loguru import logger
from config import settings       
from tradebot.application.parser import BasicSignalParser
from tradebot.application.order_generator import SimpleOrderGenerator
from tradebot.infrastructure.mt5_engine import MetaTraderEngine
from tradebot.infrastructure.telegram_listener import TelegramSignalListener

def bootstrap():

    logger.add("tradebot.log", rotation="25 MB", level="DEBUG")

    parser           = BasicSignalParser()
    engine           = MetaTraderEngine()
    order_generator  = SimpleOrderGenerator()

    gateway          = TelegramSignalListener(
        parser,
        engine,
        order_generator,
    )
    gateway.run()

if __name__ == "__main__":
    bootstrap()
