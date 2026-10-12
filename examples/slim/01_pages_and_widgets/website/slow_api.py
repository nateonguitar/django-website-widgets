import asyncio
import time


class SlowApi:
    """
    Stands in for an HTTP call to another service that takes `SECONDS` to answer. A call like this
    is what gathering in a parent speeds up: Django's async ORM runs every query on one shared
    thread, so gathered database queries still run one at a time.
    """

    SECONDS = 0.2

    @classmethod
    async def call(cls):
        await asyncio.sleep(cls.SECONDS)

    @staticmethod
    def start_clock(page: dict):
        page['request_started'] = time.perf_counter()

    @staticmethod
    def elapsed_ms(page: dict) -> int:
        """Milliseconds since `start_clock()` was called on this page context."""
        return round((time.perf_counter() - page['request_started']) * 1000)
