import asyncio
from dataclasses import dataclass

from website_widgets import register_url

from website.pages.example_page import ExamplePage
from website.slow_api import SlowApi
from website.widgets.book_list.book_list import BookList
from website.widgets.query_card.query_card import QueryCard
from website.widgets.slow_query_card.slow_query_card import SlowQueryCard
from website.widgets.sync_orm_trap_note.sync_orm_trap_note import SyncOrmTrapNote


@dataclass(frozen=True)
class CallTiming:
    """When one slow call started and finished, in milliseconds since the page started building."""

    label: str
    started_ms: int
    finished_ms: int


@register_url('async/')
class AsyncPage(ExamplePage):
    page_title = 'Async widgets'
    page_description = 'Awaiting in set_context(): the async ORM, and slow calls one after another or together.'

    LABELS = ('Call A', 'Call B', 'Call C')

    async def set_context(self):
        super().set_context()
        self.context.data['call_ms'] = round(SlowApi.SECONDS * 1000)
        SlowApi.start_clock(self.context.page)

        # Runs before any child's set_context(), so these finish first.
        timings = await asyncio.gather(*(self._timed_call(label) for label in self.LABELS))
        self.context.children['together'] = [
            QueryCard(
                label=timing.label,
                started_ms=timing.started_ms,
                finished_ms=timing.finished_ms)
            for timing in timings
        ]
        self.context.children['one_after_another'] = [SlowQueryCard(label) for label in self.LABELS]
        self.context.children['book_list'] = BookList()
        self.context.children['sync_orm_trap_note'] = SyncOrmTrapNote()

    async def _timed_call(self, label: str) -> CallTiming:
        started_ms = SlowApi.elapsed_ms(self.context.page)
        await SlowApi.call()
        return CallTiming(
            label=label,
            started_ms=started_ms,
            finished_ms=SlowApi.elapsed_ms(self.context.page))
