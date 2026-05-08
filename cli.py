"""Command-line interface for the Binance Futures Testnet trading bot."""

from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from bot.client import BinanceFuturesClient
from bot.exceptions import InvalidInputError, TradingBotError
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import ValidatedOrder, validate_order_request
from config import get_settings


app = typer.Typer(add_completion=False, help="Binance Futures Testnet trading bot.")
console = Console()


def _build_order_manager(verbose: bool = False) -> OrderManager:
    settings = get_settings()
    setup_logging(settings.log_file, verbose=verbose)
    client = BinanceFuturesClient(settings=settings)
    return OrderManager(client)


def _needs_prompt(*values: Any) -> bool:
    return any(value is None for value in values)


def _collect_order_input(
    symbol: str | None,
    side: str | None,
    order_type: str | None,
    quantity: float | None,
    price: float | None,
    stop_price: float | None,
) -> tuple[ValidatedOrder, bool]:
    prompted = _needs_prompt(symbol, side, order_type, quantity)

    raw_symbol = symbol or Prompt.ask("Symbol", default="BTCUSDT")
    raw_side = side or Prompt.ask("Side", choices=["BUY", "SELL"], default="BUY")
    raw_type = order_type or Prompt.ask(
        "Order type",
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        default="MARKET",
    )

    normalized_preview = str(raw_type).strip().upper().replace("-", "_").replace(" ", "_")
    raw_quantity = quantity
    if raw_quantity is None:
        raw_quantity = Prompt.ask("Quantity")

    raw_price: float | str | None = price
    raw_stop_price: float | str | None = stop_price

    if normalized_preview in {"LIMIT", "STOP_LIMIT"} and raw_price is None:
        prompted = True
        raw_price = Prompt.ask("Limit price")

    if normalized_preview == "STOP_LIMIT" and raw_stop_price is None:
        prompted = True
        raw_stop_price = Prompt.ask("Stop price")

    return (
        validate_order_request(
            symbol=raw_symbol,
            side=raw_side,
            order_type=raw_type,
            quantity=raw_quantity,
            price=raw_price,
            stop_price=raw_stop_price,
        ),
        prompted,
    )


def _render_order_summary(order: ValidatedOrder) -> None:
    lines = [
        f"Symbol: {order.symbol}",
        f"Side: {order.side}",
        f"Type: {order.order_type}",
        f"Quantity: {order.quantity}",
    ]
    if order.price is not None:
        lines.append(f"Price: {order.price}")
    if order.stop_price is not None:
        lines.append(f"Stop price: {order.stop_price}")

    console.print(Panel("\n".join(lines), title="Order Request", border_style="cyan"))


def _render_order_response(response: dict[str, Any]) -> None:
    table = Table(title="Order Response")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    for key in ("orderId", "symbol", "side", "type", "status", "executedQty", "avgPrice"):
        table.add_row(key, str(response.get(key, "N/A")))

    console.print(table)


@app.command()
def order(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="Trading pair, e.g. BTCUSDT."),
    side: str | None = typer.Option(None, "--side", help="BUY or SELL."),
    order_type: str | None = typer.Option(None, "--type", "-t", help="MARKET, LIMIT, or STOP_LIMIT."),
    quantity: float | None = typer.Option(None, "--quantity", "-q", help="Order quantity."),
    price: float | None = typer.Option(None, "--price", "-p", help="Required for LIMIT and STOP_LIMIT."),
    stop_price: float | None = typer.Option(None, "--stop-price", help="Required for STOP_LIMIT."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation in interactive mode."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs in the console."),
) -> None:
    """Place a market, limit, or stop-limit order."""

    try:
        validated, prompted = _collect_order_input(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        _render_order_summary(validated)

        if prompted and not yes and not Confirm.ask("Place this order?", default=False):
            console.print("[yellow]Order cancelled.[/yellow]")
            raise typer.Exit(code=0)

        manager = _build_order_manager(verbose=verbose)
        with console.status("Submitting order to Binance Futures Testnet..."):
            response = manager.place_order(
                symbol=validated.symbol,
                side=validated.side,
                order_type=validated.order_type,
                quantity=str(validated.quantity),
                price=str(validated.price) if validated.price is not None else None,
                stop_price=str(validated.stop_price) if validated.stop_price is not None else None,
            )

        _render_order_response(response)
        console.print("[green]Order placed successfully.[/green]")
    except InvalidInputError as exc:
        console.print(f"[red]Invalid input:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    except TradingBotError as exc:
        console.print(f"[red]Order failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs in the console."),
) -> None:
    """Check Binance connectivity and account balance."""

    try:
        settings = get_settings()
        setup_logging(settings.log_file, verbose=verbose)
        client = BinanceFuturesClient(settings=settings)

        with console.status("Checking Binance Futures Testnet status..."):
            ping_ok = client.ping()
            account = client.get_account_info()

        console.print("[green]Connectivity OK.[/green]" if ping_ok else "[red]Connectivity failed.[/red]")
        balances = Table(title="Account Assets")
        balances.add_column("Asset", style="cyan", no_wrap=True)
        balances.add_column("Wallet Balance", justify="right")
        balances.add_column("Available Balance", justify="right")

        for asset in account.get("assets", []):
            wallet_balance = float(asset.get("walletBalance", 0))
            available_balance = float(asset.get("availableBalance", 0))
            if wallet_balance or available_balance or asset.get("asset") == "USDT":
                balances.add_row(
                    asset.get("asset", "N/A"),
                    asset.get("walletBalance", "0"),
                    asset.get("availableBalance", "0"),
                )

        console.print(balances)
    except TradingBotError as exc:
        console.print(f"[red]Status check failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
