from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.pages.page_superclasses import ExamplePageComplex
from website_widgets.example.widgets.info_card.info_card import InfoCard
from website_widgets.example.widgets.async_widget.async_widget import AsyncWidget


class WidgetCompositionPage(ExamplePageComplex):
    """
    Example page demonstrating widget composition.
    Uses the default base template from ExampleAppPage.
    """

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        self.context.page['title'] = 'Widget Composition'
        self.context.page['nav_item'] = NavItem.WIDGET_COMPOSITION
        self.context.page['show_appbar_back_button'] = True

        # the Complex super class setts appbar/footer automatically
        # self.context.children['appbar'] = ExampleAppbar(parent=self).html_sync()
        # self.context.children['footer'] = ExampleFooter(parent=self).html_sync()

        cards_data = [
            {'title': 'First Card', 'content': 'Data is passed explicitly to each widget via constructor parameters.'},
            {'title': 'Second Card', 'content': 'Widgets are instantiated with parent=self to establish the hierarchy.'},
            {'title': 'Third Card', 'content': 'The system automatically calls html() on each widget during rendering.'},
        ]

        card_widgets = []
        for card in cards_data:
            card_widget = InfoCard(
                title=card['title'],
                content=card['content'],
                parent=self)
            card_widgets.append(card_widget)

        self.context.children['cards'] = card_widgets

        # Add async widget to demonstrate async html() support
        self.context.children['async_demo'] = AsyncWidget(
            message='Async Widget Demo',
            parent=self)
