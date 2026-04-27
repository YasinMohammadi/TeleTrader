"""Cancel bot pending orders that stay unfilled longer than a per-user limit."""

from __future__ import annotations

import threading
import time
from datetime import datetime

import MetaTrader5 as mt5
from loguru import logger

from config import settings
from .db import get_enabled_users
from ._mt5_utils import ensure_mt5

# Bot pending orders are tagged so we never cancel manual pendings.
BOT_PENDING_COMMENT_PREFIX = "TT|"
MT5_ORDER_COMMENT_MAX_LEN = 31


def _pending_types() -> set[int]:
    types = []
    for name in (
        "ORDER_TYPE_BUY_LIMIT",
        "ORDER_TYPE_SELL_LIMIT",
        "ORDER_TYPE_BUY_STOP",
        "ORDER_TYPE_SELL_STOP",
        "ORDER_TYPE_BUY_STOP_LIMIT",
        "ORDER_TYPE_SELL_STOP_LIMIT",
    ):
        v = getattr(mt5, name, None)
        if v is not None:
            types.append(int(v))
    return set(types)


_PENDING_TYPES = _pending_types()


def _order_setup_epoch(ord_) -> float | None:
    """Return order placement time as Unix seconds, or None if unknown."""
    raw = getattr(ord_, "time_setup", None)
    if isinstance(raw, datetime):
        return float(raw.timestamp())
    if isinstance(raw, (int, float)) and raw > 0:
        v = float(raw)
        # Some builds use milliseconds
        if v > 1e12:
            return v / 1000.0
        if v > 1e11:
            return v / 1000.0
        return v
    msc = getattr(ord_, "time_setup_msc", None)
    if msc is not None and int(msc) > 0:
        return float(int(msc)) / 1000.0
    return None


def _server_now_epoch() -> float | None:
    """Best-effort current broker/server Unix seconds from MT5 tick stream."""
    tick = mt5.symbol_info_tick("XAUUSD")
    if tick:
        t = getattr(tick, "time", None)
        if isinstance(t, (int, float)) and float(t) > 0:
            return float(t)
        tm = getattr(tick, "time_msc", None)
        if isinstance(tm, (int, float)) and float(tm) > 0:
            return float(tm) / 1000.0
    return None


class PendingOrderExpirer:
    """Remove unfilled pending orders older than each user's configured minutes."""

    def __init__(self, interval_sec: int = 30):
        self.interval_sec = interval_sec
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        # When MT5 omits time_setup, age from first time this process saw the order
        self._first_seen: dict[tuple[int, int], float] = {}

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(
            target=self._loop, name="pending-order-expirer", daemon=True)
        self._worker.start()
        logger.info("Pending order expirer started")

    def stop(self) -> None:
        self._stop.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=max(self.interval_sec, 2))
        logger.info("Pending order expirer stopped")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception as exc:
                logger.error(f"Pending expirer loop error: {exc}")
            self._stop.wait(self.interval_sec)

    def run_once(self) -> None:
        dbp = settings.db_path
        local_now = time.time()
        for user in get_enabled_users(dbp):
            limit_min = int(getattr(user, "pending_expire_minutes", 0) or 0)
            if limit_min <= 0:
                continue

            max_age_sec = float(limit_min * 60)
            ensure_mt5(user.mt5_path)
            if not mt5.login(
                    user.mt5_account, user.mt5_password, user.mt5_server):
                logger.warning(
                    f"Pending expirer: login failed for {user.mt5_account}")
                continue

            server_now = _server_now_epoch()
            now = server_now if server_now is not None else local_now

            orders = mt5.orders_get() or []
            live_keys: set[tuple[int, int]] = set()
            for ord_ in orders:
                otype = int(getattr(ord_, "type", -1))
                if otype not in _PENDING_TYPES:
                    continue
                comment = (getattr(ord_, "comment", "") or "").strip()
                if not comment.startswith(BOT_PENDING_COMMENT_PREFIX):
                    continue

                ticket = int(getattr(ord_, "ticket", 0))
                acct = int(user.mt5_account)
                key = (acct, ticket)
                live_keys.add(key)

                setup_epoch = _order_setup_epoch(ord_)
                if setup_epoch is not None and setup_epoch > 0:
                    self._first_seen.pop(key, None)
                    age = now - setup_epoch
                    setup_src = "time_setup"
                else:
                    if key not in self._first_seen:
                        self._first_seen[key] = now
                        logger.debug(
                            f"Pending expirer: order {ticket} has no usable "
                            f"time_setup — ageing from first bot observation")
                    age = now - self._first_seen[key]
                    setup_src = "first_seen"

                logger.debug(
                    f"Pending expirer: ticket={ticket} account={acct} "
                    f"comment='{comment}' age_min={age/60:.2f} "
                    f"limit_min={limit_min} source={setup_src}")
                if setup_src == "time_setup" and server_now is not None:
                    skew = server_now - local_now
                    if abs(skew) > 120:
                        logger.debug(
                            f"Pending expirer: using server time due to local skew "
                            f"{skew/60:.1f} min")

                if age < max_age_sec:
                    logger.debug(
                        f"Pending expirer: keep order {ticket} "
                        f"(age {age/60:.2f}m < {limit_min}m)")
                    continue

                symbol = getattr(ord_, "symbol", "") or ""
                req = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": ticket,
                    "symbol": symbol,
                }
                res = mt5.order_send(req)
                if res and int(res.retcode) == int(mt5.TRADE_RETCODE_DONE):
                    self._first_seen.pop(key, None)
                    logger.info(
                        f"Pending expirer: removed order {ticket} {symbol} "
                        f"(age {age/60:.1f} min ≥ {limit_min} min) "
                        f"account {acct}")
                else:
                    logger.warning(
                        f"Pending expirer: failed remove {ticket} "
                        f"account {acct}: "
                        f"{res._asdict() if res and hasattr(res, '_asdict') else mt5.last_error()}"
                    )

            # Drop stale first-seen entries (order gone or filled)
            stale = [k for k in self._first_seen if k[0] == user.mt5_account
                     and k not in live_keys]
            for k in stale:
                self._first_seen.pop(k, None)
