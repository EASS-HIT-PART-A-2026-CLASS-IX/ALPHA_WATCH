import asyncio
import logging
import os

from app.database import init_db
from app.refresh import refresh_saved_stocks

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = int(os.getenv("WORKER_REFRESH_INTERVAL_SECONDS", "300"))


async def run_worker() -> None:
    init_db()
    logger.info("AlphaWatch worker started; interval=%ss", REFRESH_INTERVAL_SECONDS)
    while True:
        results = await refresh_saved_stocks()
        refreshed = sum(1 for result in results if result.refreshed)
        skipped = sum(1 for result in results if result.status == "skipped")
        errors = sum(1 for result in results if result.status == "error")
        logger.info(
            "refresh cycle complete: symbols=%s refreshed=%s skipped=%s errors=%s",
            len(results),
            refreshed,
            skipped,
            errors,
        )
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
