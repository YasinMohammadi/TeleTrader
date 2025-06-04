# tradebot/application/parser.py

"""
Pure‐python parser - no telegram dependency - easy to unit‐test.
"""
import re
from typing import Sequence, List
from tradebot.domain.models import Signal, Target
from tradebot.domain.ports import SignalParserPort
from loguru import logger

# FIXED: use \s* for whitespace, not \\s*
_FIRST_LINE = re.compile(r"([A-Z]{3,6})\s*-\s*(BUY|SELL)\s*(LIMIT|MARKET)?", re.I)
_FLOAT      = r"[0-9]+(?:\.[0-9]+)?"

class BasicSignalParser(SignalParserPort):
    def parse(self, message: str) -> Signal | None:
        try:
            lines = [ln.strip() for ln in message.splitlines() if ln.strip()]
            first = _FIRST_LINE.search(lines[0])
            if not first:
                return None

            symbol     = first.group(1).upper()
            side       = first.group(2).lower()
            order_type = first.group(3).lower() if first.group(3) else "market"

            entry_text = _find(lines, "Entry")
            entry      = float(re.search(_FLOAT, entry_text).group())

            
            sl = None
            try:
                sl_text = _find(lines, "Stoploss")
                sl = float(re.search(_FLOAT, sl_text).group())
            except StopIteration:
                # No stoploss provided
                sl = None

            tgt_block  = _collect_targets(lines)
            targets    = [Target(float(re.search(_FLOAT, t).group())) for t in tgt_block]

            comment = ""
            trader_lines = [ln for ln in lines if "Trader:" in ln]
            if trader_lines:
                raw = trader_lines[-1]
                # Extract part after 'Trader:'
                part = raw.split("Trader:", 1)[1]
                # Strip non-alphanumeric and whitespace
                cleaned = re.sub(r"[^A-Za-z0-9 ]", "", part)
                comment = cleaned.strip()

            return Signal(symbol, side, order_type,
                          entry, targets, sl, comment, message)
        
        except Exception as exc:
            logger.error("parser error: {}", exc)
            return None

def _find(lines: list[str], keyword: str) -> str:
    return next(ln for ln in lines if keyword.lower() in ln.lower())

def _collect_targets(lines: list[str]) -> List[str]:
    """
    Return only the lines *immediately* after the 'Targets' header
    that are *exactly* numeric (e.g. '3333.00'), stopping as soon
    as we hit any non-numeric line (like 'Stoploss...').
    """
    idx = next(i for i, l in enumerate(lines) if "target" in l.lower())
    targets: List[str] = []
    for line in lines[idx+1:]:
        # only pure numbers allowed
        if re.fullmatch(_FLOAT, line):
            targets.append(line)
        else:
            break
    return targets
