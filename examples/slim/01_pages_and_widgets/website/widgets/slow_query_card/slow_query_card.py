from website.slow_api import SlowApi
from website.widgets.query_card.query_card import QueryCard


class SlowQueryCard(QueryCard):
    """
    Makes its own slow call in an `async def set_context()`. The library finishes each widget's
    `set_context()` before starting the next, so several of these run one after another.

    Renders its base class's template: the lookup finds `query_card.html` beside the base's module.
    """

    template_filename = 'query_card.html'

    async def set_context(self):
        self.started_ms = SlowApi.elapsed_ms(self.context.page)
        await SlowApi.call()
        self.finished_ms = SlowApi.elapsed_ms(self.context.page)
        super().set_context()
