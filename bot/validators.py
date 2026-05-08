"""Validation helpers for CLI input and order parameters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from bot.exceptions import InvalidInputError


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


@dataclass(frozen=True)
class ValidatedOrder:
    """Normalized order data ready for request construction."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None


def validate_symbol(symbol: str | None, allowed_symbols: Iterable[str] | None = None) -> str:
    """Validate and normalize a USDT-M futures symbol."""

    if symbol is None or not str(symbol).strip():
        raise InvalidInputError("Symbol is required.")

    normalized = str(symbol).strip().upper()
    if not SYMBOL_PATTERN.match(normalized):
        raise InvalidInputError("Symbol must contain only letters/numbers, e.g. BTCUSDT.")
    if not normalized.endswith("USDT"):
        raise InvalidInputError("Only USDT-M futures symbols are supported, e.g. BTCUSDT.")

    if allowed_symbols is not None:
        allowed = {item.upper() for item in allowed_symbols}
        if normalized not in allowed:
            supported = ", ".join(sorted(allowed))
            raise InvalidInputError(f"Unsupported symbol {normalized}. Supported: {supported}.")

    return normalized


def validate_side(side: str | None) -> str:
    """Validate and normalize the order side."""

    if side is None or not str(side).strip():
        raise InvalidInputError("Side is required. Use BUY or SELL.")

    normalized = str(side).strip().upper()
    if normalized not in VALID_SIDES:
        raise InvalidInputError("Side must be BUY or SELL.")
    return normalized


def validate_order_type(order_type: str | None) -> str:
    """Validate and normalize the order type."""

    if order_type is None or not str(order_type).strip():
        raise InvalidInputError("Order type is required. Use MARKET, LIMIT, or STOP_LIMIT.")

    normalized = str(order_type).strip().upper().replace("-", "_").replace(" ", "_")
    if normalized not in VALID_ORDER_TYPES:
        raise InvalidInputError("Order type must be MARKET, LIMIT, or STOP_LIMIT.")
    return normalized


def validate_positive_decimal(value: str | int | float | Decimal | None, field_name: str) -> Decimal:
    """Validate that a numeric field is present and greater than zero."""

    if value is None or (isinstance(value, str) and not value.strip()):
        raise InvalidInputError(f"{field_name} is required.")

    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise InvalidInputError(f"{field_name} must be a number.") from None

    if decimal_value <= 0:
        raise InvalidInputError(f"{field_name} must be greater than zero.")

    return decimal_value


def validate_quantity(quantity: str | int | float | Decimal | None) -> Decimal:
    """Validate an order quantity."""

    return validate_positive_decimal(quantity, "Quantity")


def validate_price(price: str | int | float | Decimal | None) -> Decimal:
    """Validate a limit price."""

    return validate_positive_decimal(price, "Price")


def validate_stop_price(stop_price: str | int | float | Decimal | None) -> Decimal:
    """Validate a stop trigger price."""

    return validate_positive_decimal(stop_price, "Stop price")


def decimal_to_str(value: Decimal) -> str:
    """Format Decimal values for Binance without scientific notation."""

    return format(value.normalize(), "f")


def validate_order_request(
    symbol: str | None,
    side: str | None,
    order_type: str | None,
    quantity: str | int | float | Decimal | None,
    price: str | int | float | Decimal | None = None,
    stop_price: str | int | float | Decimal | None = None,
    allowed_symbols: Iterable[str] | None = None,
) -> ValidatedOrder:
    """Validate a complete order request and return normalized values."""

    normalized_type = validate_order_type(order_type)
    normalized_price = None
    normalized_stop_price = None

    if normalized_type in {"LIMIT", "STOP_LIMIT"}:
        normalized_price = validate_price(price)

    if normalized_type == "STOP_LIMIT":
        normalized_stop_price = validate_stop_price(stop_price)

    return ValidatedOrder(
        symbol=validate_symbol(symbol, allowed_symbols=allowed_symbols),
        side=validate_side(side),
        order_type=normalized_type,
        quantity=validate_quantity(quantity),
        price=normalized_price,
        stop_price=normalized_stop_price,
    )
