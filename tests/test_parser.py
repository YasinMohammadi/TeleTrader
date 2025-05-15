import pytest
from tradebot.application.parser import BasicSignalParser

SAMPLES = [  # text, symbol, side, order_type, entry, stop_loss, targets, comment
    (
        """
        ⚜️ XAUUSD - BUY LIMIT

        🛒 Entry : 3322/3319

        🎯 Targets :
        3327
        3333
        3338

        🔺 Stoploss : 3313

        💰 @Jasin  Trader:Lily 💰
        """,
        "XAUUSD", "buy",  "limit", 3322.00, 3313.00,
        [3327.0, 3333.0, 3338.0],
        "Lily"
    ),
    (
        "EURUSD - BUY LIMIT\nEntry : 1.1000\nTargets :\n1.1010\nStoploss : 1.0980",
        "EURUSD", "buy", "limit", 1.1000, 1.0980,
        [1.1010],
        ""
    ),
    (
        """
        ⚜️ XAUUSD - SELL NOW

        🛒 Entry : 3278

        🎯 Targets :
        3275
        3270
        3260

        💰 @Jasin Trader: Empire💰
        """,
        "XAUUSD", "sell", "market", 3278.0, None,
        [3275.0, 3270.0, 3260.0],
        "Empire"
    ),
    (
        """
        ⚜️ XAUUSD - SELL NOW 

        🛒 Entry : 3275-3280 

        🎯 Targets : 
        3272
        3270
        3267
        3264
        3250 

        🔺 Stoploss :3290 

        💰 @Jasin Trader: Nemat💰
        """,
        "XAUUSD", "sell", "market", 3275.0, 3290.0,
        [3272.0, 3270.0, 3267.0, 3264.0, 3250.0],
        "Nemat"
    ),
    (
        """
        ⚜️ XAUUSD - BUY LIMIT 

        🛒 Entry : 3284 

        🎯 Targets : 
        3286
        3288
        3290
        3293
        3295
        3300
        3305 

        💰 @Jasin Trader: Nemat💰
        """,
        "XAUUSD", "buy", "limit", 3284.0, None,
        [3286.0, 3288.0, 3290.0, 3293.0, 3295.0, 3300.0, 3305.0],
        "Nemat"
    ),
    (
        """
        ⚜️ XAUUSD - SELL NOW

        🛒 Entry : 3224

        🎯 Targets :
        3220
        3215
        3210
        3205
        3200

        🔺 Stoploss : 3235**

        💰 @Jasin Trader: Empire💰
        """,
        "XAUUSD", "sell", "market", 3224.0, 3235.0,
        [3220.0, 3215.0, 3210.0, 3205.0, 3200.0],
        "Empire"
    ),
]

@pytest.mark.parametrize(
    "text,symbol,side,order_type,entry,stop_loss,targets,comment",
    SAMPLES
)
def test_parser_various(text, symbol, side, order_type, entry, stop_loss, targets, comment):
    """
    Smoke test across multiple signal formats, now checks comment too.
    """
    sig = BasicSignalParser().parse(text)
    assert sig is not None, "Parser returned None for a valid signal"
    assert sig.symbol     == symbol
    assert sig.side       == side
    assert sig.order_type == order_type
    assert sig.entry      == entry
    assert sig.stop_loss  == stop_loss
    assert [t.price for t in sig.targets] == targets
    assert sig.comment    == comment


def test_parser_invalid_returns_none():
    assert BasicSignalParser().parse("this is not a trade signal") is None
