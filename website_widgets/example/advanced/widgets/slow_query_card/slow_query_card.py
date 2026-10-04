from website_widgets.example.advanced.mock_query import MockQuery
from website_widgets.example.advanced.widgets.query_card.query_card import QueryCard


class SlowQueryCard(QueryCard):
    """
    Runs its own mock query in an `async def set_context()`. The library awaits each widget's
    `set_context()` before starting the next, so several of these run one after another.

    Renders its base class's template: the lookup finds `query_card.html` beside the base's module.
    """

    template_filename = 'query_card.html'

    def __init__(self, label: str):
        super().__init__(label)

    async def set_context(self):
        self.started_ms = MockQuery.elapsed_ms(self.context.page)
        await MockQuery.run()
        self.finished_ms = MockQuery.elapsed_ms(self.context.page)
        super().set_context()
