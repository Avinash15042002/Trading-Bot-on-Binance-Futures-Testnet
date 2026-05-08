"""Custom exceptions used across the trading bot."""


class TradingBotError(Exception):
    """Base class for application-level errors."""


class InvalidInputError(TradingBotError):
    """Raised when CLI or order input fails validation."""


class APIConnectionError(TradingBotError):
    """Raised when the Binance API cannot be reached or initialized."""


class OrderPlacementError(TradingBotError):
    """Raised when Binance rejects or fails an order placement request."""


class InsufficientBalanceError(OrderPlacementError):
    """Raised when an order cannot be placed because funds are insufficient."""
