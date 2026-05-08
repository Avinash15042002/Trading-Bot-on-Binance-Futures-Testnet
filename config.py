"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

from bot.exceptions import InvalidInputError


ROOT_DIR = Path(__file__).resolve().parent
TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_LOG_FILE = ROOT_DIR / "logs" / "trading_bot.log"
DEFAULT_SUPPORTED_SYMBOLS: Tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "AVAXUSDT",
    "TRXUSDT",
    "MATICUSDT",
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for Binance Futures Testnet access."""

    api_key: str | None
    api_secret: str | None
    base_url: str = TESTNET_BASE_URL
    default_symbol: str = DEFAULT_SYMBOL
    log_file: Path = DEFAULT_LOG_FILE
    supported_symbols: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_SUPPORTED_SYMBOLS)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from .env and process environment variables."""

        load_dotenv(ROOT_DIR / ".env")
        supported_symbols = os.getenv("SUPPORTED_SYMBOLS")
        if supported_symbols:
            symbols = tuple(
                symbol.strip().upper()
                for symbol in supported_symbols.split(",")
                if symbol.strip()
            )
        else:
            symbols = DEFAULT_SUPPORTED_SYMBOLS

        return cls(
            api_key=os.getenv("BINANCE_TESTNET_API_KEY"),
            api_secret=os.getenv("BINANCE_TESTNET_API_SECRET"),
            base_url=os.getenv("BINANCE_TESTNET_BASE_URL", TESTNET_BASE_URL),
            default_symbol=os.getenv("DEFAULT_SYMBOL", DEFAULT_SYMBOL).upper(),
            log_file=Path(os.getenv("TRADING_BOT_LOG_FILE", DEFAULT_LOG_FILE)),
            supported_symbols=symbols,
        )

    def require_credentials(self) -> None:
        """Raise a clear error if Binance API credentials are missing."""

        if not self.api_key or not self.api_secret:
            raise InvalidInputError(
                "Missing Binance Futures Testnet credentials. "
                "Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET in .env."
            )


def get_settings() -> Settings:
    """Return settings loaded from the current environment."""

    return Settings.from_env()
