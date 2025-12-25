from website_widgets.example.pages.app_page import ExampleAppPageSimple
from website_widgets.example.widgets.info_card.info_card import InfoCard


class WidgetCompositionPage(ExampleAppPageSimple):
    """
    Example page demonstrating widget composition.
    Uses the default base template from ExampleAppPage.
    """

    async def set_context(self, *args, **kwargs):
        self.context.page.set('title', 'Widget Composition')
        self.context.page.set('show_parent_link', True)

        cards_data = [
            {'title': 'First Card', 'content': 'Data is passed explicitly to each widget via html() parameters.'},
            {'title': 'Second Card', 'content': 'No parent data inheritance - clean prop drilling.'},
            {'title': 'Third Card', 'content': 'Each widget manages its own context independently.'},
        ]

        card_widgets = []
        for card in cards_data:
            widget = InfoCard(parent=self)
            card_html = widget.html_sync(title=card['title'], content=card['content'])
            card_widgets.append(card_html)

        self.context.children.set('cards', card_widgets)
