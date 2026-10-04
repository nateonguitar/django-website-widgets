import asyncio
import time


class MockQuery:
    """Stands in for an awaited database query that takes `SECONDS` to answer."""

    SECONDS = 0.2

    @classmethod
    async def run(cls):
        await asyncio.sleep(cls.SECONDS)

    @staticmethod
    def start_clock(page: dict):
        page['request_started'] = time.perf_counter()

    @staticmethod
    def elapsed_ms(page: dict) -> int:
        """Milliseconds since `start_clock()` was called on this page context."""
        return round((time.perf_counter() - page['request_started']) * 1000)
