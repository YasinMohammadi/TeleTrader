import pytest
from tradebot.application.order_generator import OrderGenerator
from tradebot.domain.models import Signal, Target

# -------------------------------------------------------------
# Fixtures & helpers
# -------------------------------------------------------------

FIXED_RISK = 1.0  # total lots per signal

def fixed_risk(_signal):
    return FIXED_RISK

@pytest.fixture
def generator():
    return OrderGenerator(risk_func=fixed_risk)


def make_signal(symbol, side, order_type, entry, targets, sl, comment):
    """Utility to build a Signal with arbitrary targets."""
    return Signal(
        symbol=symbol,
        side=side,
        order_type=order_type,
        entry=entry,
        targets=[Target(price=t) for t in targets],
        stop_loss=sl,
        comment=comment,
        raw_source=""
    )

# -------------------------------------------------------------
# Tests
# -------------------------------------------------------------

@pytest.mark.parametrize(
    "targets,expected_volumes", [
        ([10, 20, 30], [0.33, 0.33, 0.33]),
        ([50],         [1.0]),
    ])
def test_generate_splits_volume_equally(generator, targets, expected_volumes):
    sig = make_signal("EURUSD", "buy", "limit", 1.2345, targets, 1.2300, "test")
    orders = generator.generate(sig)
    assert len(orders) == len(targets)

    for idx, (order, exp_vol, tgt) in enumerate(zip(orders, expected_volumes, targets), start=1):
        assert pytest.approx(order.volume, rel=1e-6) == exp_vol
        assert order.price == sig.entry               # limit order retains entry price
        assert order.tp    == tgt
        assert order.sl    == sig.stop_loss
        # comment should include target index
        assert order.comment == f"{sig.comment} {idx}of{len(targets)}".strip()


@pytest.mark.parametrize("order_type,price_expected", [
    ("limit", 3.3),
    ("market", None),
])
def test_price_field_for_market_and_limit(generator, order_type, price_expected):
    tgts = [100]
    sig = make_signal("XAUUSD", "sell", order_type, 3.3, tgts, 2.9, "cmt")
    orders = generator.generate(sig)
    assert len(orders) == 1
    order = orders[0]
    assert order.price == price_expected
    # comment ends with 
    assert order.comment.endswith("1of1")


def test_no_targets_returns_empty(generator):
    sig = make_signal("BTCUSD", "buy", "market", 50000, [], None, "none")
    orders = generator.generate(sig)
    assert orders == []


def test_custom_risk_function_applied():
    def custom_risk(_):
        return 2.0
    gen = OrderGenerator(risk_func=custom_risk)
    sig = make_signal("EURUSD", "buy", "limit", 1.1, [1.2, 1.3], 1.0, "c")
    orders = gen.generate(sig)
    assert len(orders) == 2
    for idx, o in enumerate(orders, start=1):
        assert o.volume == pytest.approx(1.0)
        assert o.comment.endswith(f"{idx}of2")
