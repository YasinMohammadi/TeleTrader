# tradebot/infrastructure/telegram_listener.py

"""Telegram gateway that turns raw messages into MT5 orders."""
import asyncio

from loguru import logger
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler, filters
)
from telegram import Update

from config import settings
from tradebot.domain.ports import (
    SignalParserPort, 
    TradingEnginePort,
    OrderPort,
)
from tradebot.domain.models import Order, OrderResult, Signal


class TelegramSignalListener:
    """Listen to a signal channel, parse, generate orders, execute them."""

    def __init__(
            self,
            parser: SignalParserPort,
            engine: TradingEnginePort,
            order_generator: OrderPort
    ):
        self.parser = parser
        self.engine = engine
        self.generator = order_generator

        self.app = (ApplicationBuilder()
                    .token(settings.telegram_token)
                    .build())

        # Restrict to the configured channel only
        allowed_chat = filters.Chat(settings.signal_chat_id)
        self.app.add_handler(MessageHandler(allowed_chat, self._handle))
        self.app.add_error_handler(self._error_handler)

    # ------------------------------------------------------------------
    async def _handle(self, upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
        text = upd.effective_message.text or ""
        logger.debug("incoming text: {}", text.replace("\n", " ")[:100])

        sig: Signal | None = self.parser.parse(text)
        if sig is None:
            logger.info("parser returned None")
            return

        orders: list[Order] = self.generator.generate_orders(sig)
        if not orders:
            await upd.effective_message.reply_text("Signal parsed but generated no orders.")
            return

        responses: list[str] = []
        for order in orders:
            res: OrderResult = self.engine.execute_order(order)
            logger.debug(f"Getting Order: {order}")
            status = "OK" if res.success else "FAIL"
            responses.append(f"{order.side.upper()} {order.risk} {order.symbol} -> TP {order.tp} : {status}")

        await upd.effective_message.reply_text("\n".join(responses))

    # ------------------------------------------------------------------
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception(f"Unhandled exception: {context.error}")
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Internal error _ see logs.")

    # ------------------------------------------------------------------
    def run(self):
        logger.info("Starting Telegram polling …")
        self.app.run_polling()
