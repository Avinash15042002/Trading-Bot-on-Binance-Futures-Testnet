from decimal import Decimal

import pytest

from bot.exceptions import InvalidInputError
from bot.validators import (
    decimal_to_str,
    validate_order_request,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)


def test_validate_symbol_normalizes_usdt_symbol() -> None:
    assert validate_symbol("btcusdt") == "BTCUSDT"


@pytest.mark.parametrize("symbol", ["", "BTC/USDT", "BTCUSD", "   "])
def test_validate_symbol_rejects_invalid_values(symbol: str) -> None:
    with pytest.raises(InvalidInputError):
        validate_symbol(symbol)


def test_validate_symbol_can_use_allowed_symbol_list() -> None:
    assert validate_symbol("ethusdt", allowed_symbols=["BTCUSDT", "ETHUSDT"]) == "ETHUSDT"
    with pytest.raises(InvalidInputError):
        validate_symbol("SOLUSDT", allowed_symbols=["BTCUSDT", "ETHUSDT"])


@pytest.mark.parametrize(("raw", "expected"), [("buy", "BUY"), (" SELL ", "SELL")])
def test_validate_side_normalizes_valid_sides(raw: str, expected: str) -> None:
    assert validate_side(raw) == expected


def test_validate_side_rejects_unknown_side() -> None:
    with pytest.raises(InvalidInputError):
        validate_side("HOLD")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("market", "MARKET"), ("LIMIT", "LIMIT"), ("stop-limit", "STOP_LIMIT")],
)
def test_validate_order_type_normalizes_valid_values(raw: str, expected: str) -> None:
    assert validate_order_type(raw) == expected


def test_validate_order_type_rejects_unknown_type() -> None:
    with pytest.raises(InvalidInputError):
        validate_order_type("OCO")


@pytest.mark.parametrize("value", ["0", 0, "-1", None, "abc"])
def test_validate_quantity_rejects_non_positive_or_non_numeric_values(value: object) -> None:
    with pytest.raises(InvalidInputError):
        validate_quantity(value)  # type: ignore[arg-type]


def test_validate_quantity_accepts_positive_decimal_values() -> None:
    assert validate_quantity("0.001") == Decimal("0.001")


def test_validate_price_accepts_positive_values() -> None:
    assert validate_price("3500.50") == Decimal("3500.50")


def test_validate_order_request_allows_market_without_price() -> None:
    order = validate_order_request("BTCUSDT", "BUY", "MARKET", "0.001")

    assert order.symbol == "BTCUSDT"
    assert order.side == "BUY"
    assert order.order_type == "MARKET"
    assert order.price is None
    assert order.stop_price is None


def test_validate_order_request_requires_price_for_limit() -> None:
    with pytest.raises(InvalidInputError):
        validate_order_request("BTCUSDT", "BUY", "LIMIT", "0.001")


def test_validate_order_request_requires_stop_price_for_stop_limit() -> None:
    with pytest.raises(InvalidInputError):
        validate_order_request("BTCUSDT", "BUY", "STOP_LIMIT", "0.001", price="100000")


def test_validate_order_request_accepts_stop_limit() -> None:
    order = validate_order_request(
        "BTCUSDT",
        "BUY",
        "STOP_LIMIT",
        "0.001",
        price="100000",
        stop_price="99500",
    )

    assert order.order_type == "STOP_LIMIT"
    assert order.price == Decimal("100000")
    assert order.stop_price == Decimal("99500")


def test_decimal_to_str_avoids_scientific_notation() -> None:
    assert decimal_to_str(Decimal("0.001000")) == "0.001"
    assert decimal_to_str(Decimal("100000")) == "100000"
