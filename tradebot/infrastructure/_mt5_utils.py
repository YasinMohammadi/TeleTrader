# tradebot/infrastructure/_mt5_utils.py
import MetaTrader5 as mt5
from loguru import logger
from config import settings

def ensure_mt5():

    """Init & login once; subsequent calls are no-ops."""

    if not mt5.initialize(settings.mt5_path):
        logger.info("Couldn't Initailize MT5 Terminal")
        mt5.shutdown()
        raise RuntimeError(mt5.last_error())

    account = settings.mt_account
    if mt5.account_info() and mt5.account_info().login == account:
        logger.info(f"MT5  already logged in (account {account}). No login attempt.")
        return  

    if not mt5.login(login=account,
                        password=settings.mt_password,
                        server=settings.mt_server):
        raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")

    logger.info(f"MT5 logged in (account {account})")

    
   
