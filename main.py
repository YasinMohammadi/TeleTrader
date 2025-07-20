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
from tradebot.infrastructure.telegram_notifier import TelegramNotifier
import sys

def bootstrap():

    logger.add("tradebot.log", rotation="25 MB", level="DEBUG")

    parser           = BasicSignalParser()
    engine           = MetaTraderEngine()
    risk_manager     = FiboRiskManager(reverse=True)
    order_generator  = SimpleOrderGenerator(risk_manager=risk_manager)
    notifier         = TelegramNotifier(settings.telegram_token, settings.signal_chat_id)

    gateway          = TelegramSignalListener(
        parser,
        engine,
        order_generator,
        notifier,
    )
    try:
        gateway.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down bot.")
        try:
            import asyncio
            asyncio.run(notifier.notify("Trading bot has stopped."))
        except Exception:
            logger.error("Failed to send shutdown notification on interrupt")
        sys.exit(0)

if __name__ == "__main__":
    bootstrap()
