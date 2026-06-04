import argparse
import asyncio
import logging

from app.database import init_db
from app.refresh import DEFAULT_CONCURRENCY, DEFAULT_RETRIES, refresh_saved_stocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh AlphaWatch market data snapshots.")
    parser.add_argument(
        "symbols",
        nargs="*",
        help="Optional stock symbols to refresh. If omitted, all saved watchlist symbols are refreshed.",
    )
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    init_db()
    results = await refresh_saved_stocks(
        symbols=args.symbols or None,
        concurrency=args.concurrency,
        retries=args.retries,
    )
    if not results:
        print("No stocks to refresh. Add symbols to a watchlist or pass symbols manually.")
        return 0

    for result in results:
        detail = f" ({result.error})" if result.error else ""
        print(f"{result.symbol}: {result.status}, refreshed={result.refreshed}, attempts={result.attempts}{detail}")

    return 1 if any(result.status == "error" for result in results) else 0


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
