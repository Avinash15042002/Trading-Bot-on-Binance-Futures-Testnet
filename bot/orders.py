"""Order construction and placement logic."""

from __future__ import annotations

import logging
from typing import Any

from bot.client import BinanceFuturesClient
from bot.exceptions import OrderPlacementError
from bot.validators import (
    ValidatedOrder,
    decimal_to_str,
    validate_order_request,
)


logger = logging.getLogger(__name__)


class OrderManager:
    """Validate order input, build Binance parameters, and submit orders."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self.client = client

    def place_market_order(self, symbol: str, side: str, quantity: float | str) -> dict[str, Any]:
        """Place a MARKET order."""

        order = validate_order_request(symbol, side, "MARKET", quantity)
        return self._place_order(order)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str,
        price: float | str,
    ) -> dict[str, Any]:
        """Place a LIMIT order with GTC time-in-force."""

        order = validate_order_request(symbol, side, "LIMIT", quantity, price=price)
        return self._place_order(order)

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float | str,
        price: float | str,
        stop_price: float | str,
    ) -> dict[str, Any]:
        """Place a stop-limit order using Binance Futures STOP order type."""

        order = validate_order_request(
            symbol,
            side,
            "STOP_LIMIT",
            quantity,
            price=price,
            stop_price=stop_price,
        )
        return self._place_order(order)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float | str,
        price: float | str | None = None,
        stop_price: float | str | None = None,
    ) -> dict[str, Any]:
        """Place an order based on the user-facing order type."""

        order = validate_order_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        return self._place_order(order)

    def _place_order(self, order: ValidatedOrder) -> dict[str, Any]:
        params = self._build_params(order)
        logger.info("Placing %s order: %s", order.order_type, self._format_order_summary(params))

        try:
            response = self.client.create_order(**params)
        except OrderPlacementError:
            raise
        except Exception as exc:
            logger.exception("Order placement failed before receiving a Binance response")
            raise OrderPlacementError(f"Order placement failed: {exc}") from exc

        result = self._format_order_response(response)
        logger.info("Order placed: %s", result)
        return result

    def _build_params(self, order: ValidatedOrder) -> dict[str, str]:
        params = {
            "symbol": order.symbol,
            "side": order.side,
            "type": self._binance_order_type(order.order_type),
            "quantity": decimal_to_str(order.quantity),
        }

        if order.order_type in {"LIMIT", "STOP_LIMIT"}:
            params["timeInForce"] = "GTC"
            params["price"] = decimal_to_str(order.price)  # type: ignore[arg-type]

        if order.order_type == "STOP_LIMIT":
            params["stopPrice"] = decimal_to_str(order.stop_price)  # type: ignore[arg-type]

        return params

    @staticmethod
    def _binance_order_type(order_type: str) -> str:
        if order_type == "STOP_LIMIT":
            return "STOP"
        return order_type

    @staticmethod
    def _format_order_summary(params: dict[str, str]) -> str:
        summary_parts = [
            f"symbol={params['symbol']}",
            f"side={params['side']}",
            f"type={params['type']}",
            f"quantity={params['quantity']}",
        ]
        if "price" in params:
            summary_parts.append(f"price={params['price']}")
        if "stopPrice" in params:
            summary_parts.append(f"stopPrice={params['stopPrice']}")
        return ", ".join(summary_parts)

    @staticmethod
    def _format_order_response(response: dict[str, Any]) -> dict[str, Any]:
        return {
            "orderId": response.get("orderId"),
            "symbol": response.get("symbol"),
            "side": response.get("side"),
            "type": response.get("type"),
            "status": response.get("status"),
            "executedQty": response.get("executedQty", "0"),
            "avgPrice": response.get("avgPrice") or response.get("avgFillPrice") or "N/A",
            "rawResponse": response,
        }
