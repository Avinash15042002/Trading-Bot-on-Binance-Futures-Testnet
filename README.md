# Binance Futures Testnet Trading Bot

A CLI-based Python trading bot for Binance USDT-M Futures Testnet. It places market, limit, and stop-limit orders with validation, structured logging, and clear terminal output.

## Features

- Market and limit orders on Binance Futures Testnet
- BUY and SELL support
- Stop-limit orders as a bonus order type
- Interactive prompt mode when required order inputs are omitted
- Structured logs for API requests, responses, and errors
- Unit tests for validation and mocked order placement

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add Binance Futures Testnet credentials:

```bash
copy .env.example .env
```

4. Confirm the CLI is available:

```bash
python cli.py --help
```

## Usage

Place a market order:

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Place a limit order:

```bash
python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
```

Place a stop-limit order:

```bash
python cli.py order --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.001 --price 100000 --stop-price 99500
```

Use interactive mode:

```bash
python cli.py order
```

Check connectivity and balances:

```bash
python cli.py status
```

## Logging

Logs are written to `logs/trading_bot.log`. The log file records API requests, responses, and errors. Live MARKET and LIMIT order evidence will appear there after running those commands with valid testnet credentials.

## Tests

Run the unit tests:

```bash
pytest tests/ -v
```

## Assumptions

- This app targets Binance Futures Testnet, not production Binance.
- Credentials must be generated from a Binance Futures Testnet account.
- The configured base URL is `https://testnet.binancefuture.com`.
- The CLI validates input locally before making order placement requests.
- Exchange-level filters such as minimum notional and symbol precision are still enforced by Binance.
