from typing import Any

import pytest

from bot.exceptions import InvalidInputError, OrderPlacementError
from bot.orders import OrderManager


class FakeFuturesClient:
    def __init__(self, response: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.response = response or {
            "orderId": 12345,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
        }
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def create_order(self, **params: Any) -> dict[str, Any]:
        self.requests.append(params)
        if self.error:
            raise self.error
        return self.response


def test_place_market_order_builds_expected_request() -> None:
    client = FakeFuturesClient()
    manager = OrderManager(client)  # type: ignore[arg-type]

    result = manager.place_market_order("btcusdt", "buy", "0.001")

    assert client.requests == [
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.001",
        }
    ]
    assert result["orderId"] == 12345
    assert result["status"] == "NEW"


def test_place_limit_order_builds_expected_request() -> None:
    client = FakeFuturesClient(
        response={
            "orderId": 23456,
            "symbol": "ETHUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
        }
    )
    manager = OrderManager(client)  # type: ignore[arg-type]

    result = manager.place_limit_order("ETHUSDT", "SELL", "0.01", "3500")

    assert client.requests == [
        {
            "symbol": "ETHUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "quantity": "0.01",
            "timeInForce": "GTC",
            "price": "3500",
        }
    ]
    assert result["orderId"] == 23456
    assert result["type"] == "LIMIT"


def test_place_stop_limit_order_maps_to_binance_stop_request() -> None:
    client = FakeFuturesClient(
        response={
            "orderId": 34567,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "STOP",
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
        }
    )
    manager = OrderManager(client)  # type: ignore[arg-type]

    result = manager.place_stop_limit_order("BTCUSDT", "BUY", "0.001", "100000", "99500")

    assert client.requests == [
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "STOP",
            "quantity": "0.001",
            "timeInForce": "GTC",
            "price": "100000",
            "stopPrice": "99500",
        }
    ]
    assert result["type"] == "STOP"


def test_place_order_rejects_invalid_input_before_client_call() -> None:
    client = FakeFuturesClient()
    manager = OrderManager(client)  # type: ignore[arg-type]

    with pytest.raises(InvalidInputError):
        manager.place_order("BTCUSD", "BUY", "MARKET", "0.001")

    assert client.requests == []


def test_place_order_wraps_unexpected_client_errors() -> None:
    client = FakeFuturesClient(error=RuntimeError("network down"))
    manager = OrderManager(client)  # type: ignore[arg-type]

    with pytest.raises(OrderPlacementError, match="network down"):
        manager.place_market_order("BTCUSDT", "BUY", "0.001")
