# tradebot/infrastructure/_mt5_utils.py
import MetaTrader5 as mt5
from loguru import logger

def ensure_mt5(path: str):
    """
    Ensure MT5 is initialized for a specific terminal path.
    Shuts down and re-initializes if the path changes.
    """

    term_info = mt5.terminal_info()
    if term_info and term_info.path == path:
        # Already initialized with the correct path
        logger.info(f"MT5 already initialized with terminal at {path}. No re-initialization needed.")
        return

    if term_info:
        logger.info(f"Switching MT5 terminal from {term_info.path} to {path}")
        mt5.shutdown()

    if not mt5.initialize(path=path):
        logger.error(f"Couldn't initialize MT5 Terminal at path: {path}")
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")

    logger.info(f"MT5 initialized with terminal at {path}")



