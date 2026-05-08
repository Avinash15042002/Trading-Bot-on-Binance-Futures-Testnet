"""Binance Futures Testnet client wrapper."""

from __future__ import annotations

import logging
from typing import Any

from bot.exceptions import APIConnectionError, InvalidInputError, OrderPlacementError
from config import Settings, get_settings

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceRequestException
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    Client = None  # type: ignore[assignment]
    BinanceAPIException = BinanceRequestException = Exception  # type: ignore[misc,assignment]


logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Small wrapper around python-binance for USDT-M Futures Testnet."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.api_key = api_key or self.settings.api_key
        self.api_secret = api_secret or self.settings.api_secret

        if not self.api_key or not self.api_secret:
            self.settings.require_credentials()
        if Client is None:
            raise APIConnectionError(
                "python-binance is not installed. Run: pip install -r requirements.txt"
            )

        try:
            self.client = Client(self.api_key, self.api_secret, testnet=True, ping=False)
            futures_base_url = self.settings.base_url.rstrip("/")
            self.client.FUTURES_URL = f"{futures_base_url}/fapi"
            self.client.FUTURES_TESTNET_URL = f"{futures_base_url}/fapi"
            self.client.FUTURES_DATA_URL = f"{futures_base_url}/futures/data"
            self.client.FUTURES_DATA_TESTNET_URL = f"{futures_base_url}/futures/data"
        except Exception as exc:
            logger.exception("Failed to initialize Binance Futures Testnet client")
            raise APIConnectionError(f"Could not initialize Binance client: {exc}") from exc

        logger.info("Binance Futures Testnet client initialized")
        logger.debug("Futures base URL configured as %s", self.client.FUTURES_URL)

    def ping(self) -> bool:
        """Check testnet API connectivity."""

        try:
            logger.info("API request: futures_ping")
            response = self.client.futures_ping()
            logger.debug("API response: futures_ping -> %s", response)
            return True
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.exception("Binance ping failed")
            raise APIConnectionError(f"Binance ping failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Network failure during Binance ping")
            raise APIConnectionError(f"Could not reach Binance Futures Testnet: {exc}") from exc

    def get_account_info(self) -> dict[str, Any]:
        """Fetch account information and balances."""

        try:
            logger.info("API request: futures_account")
            response = self.client.futures_account()
            logger.debug("API response: futures_account -> %s", response)
            return response
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.exception("Failed to fetch Binance account information")
            raise APIConnectionError(f"Could not fetch account information: {exc}") from exc
        except Exception as exc:
            logger.exception("Network failure while fetching account information")
            raise APIConnectionError(f"Could not fetch account information: {exc}") from exc

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Return exchange metadata for a futures symbol."""

        normalized_symbol = symbol.upper()
        try:
            logger.info("API request: futures_exchange_info for %s", normalized_symbol)
            exchange_info = self.client.futures_exchange_info()
            logger.debug("API response: futures_exchange_info -> %s", exchange_info)
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.exception("Failed to fetch symbol information")
            raise APIConnectionError(f"Could not fetch symbol information: {exc}") from exc
        except Exception as exc:
            logger.exception("Network failure while fetching symbol information")
            raise APIConnectionError(f"Could not fetch symbol information: {exc}") from exc

        for item in exchange_info.get("symbols", []):
            if item.get("symbol") == normalized_symbol:
                return item

        raise InvalidInputError(f"Symbol {normalized_symbol} was not found on Binance Futures Testnet.")

    def create_order(self, **params: Any) -> dict[str, Any]:
        """Place a futures order using python-binance."""

        try:
            logger.info("API request: futures_create_order")
            logger.debug("Order request parameters: %s", params)
            response = self.client.futures_create_order(**params)
            logger.info(
                "API response: orderId=%s status=%s",
                response.get("orderId"),
                response.get("status"),
            )
            logger.debug("Full order response: %s", response)
            return response
        except BinanceAPIException as exc:
            logger.exception("Binance rejected the order")
            message = getattr(exc, "message", str(exc))
            raise OrderPlacementError(f"Binance rejected the order: {message}") from exc
        except BinanceRequestException as exc:
            logger.exception("Binance request failed")
            raise APIConnectionError(f"Binance request failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected failure while placing order")
            raise OrderPlacementError(f"Could not place order: {exc}") from exc
