import asyncio

from website_widgets.example.advanced.mock_query import MockQuery
from website_widgets.example.advanced.pages.advanced_demo_page.advanced_demo_page import AdvancedDemoPage
from website_widgets.example.advanced.widgets.query_card.query_card import QueryCard
from website_widgets.example.advanced.widgets.slow_query_card.slow_query_card import SlowQueryCard


class AsyncPage(AdvancedDemoPage):
    LABELS = ('Query A', 'Query B', 'Query C')

    async def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Async widgets'
        self.context.page['description'] = 'Awaiting in set_context(), one after another or together.'
        self.context.data['query_ms'] = round(MockQuery.SECONDS * 1000)
        MockQuery.start_clock(self.context.page)

        # Runs before any child's set_context(), so these finish first.
        timings = await asyncio.gather(*(self._timed_query(label) for label in self.LABELS))
        self.context.children['together'] = [
            QueryCard(label, started_ms, finished_ms)
            for label, started_ms, finished_ms in timings
        ]
        self.context.children['one_after_another'] = [
            SlowQueryCard(label) for label in self.LABELS
        ]

    async def _timed_query(self, label: str) -> tuple[str, int, int]:
        started_ms = MockQuery.elapsed_ms(self.context.page)
        await MockQuery.run()
        return label, started_ms, MockQuery.elapsed_ms(self.context.page)
