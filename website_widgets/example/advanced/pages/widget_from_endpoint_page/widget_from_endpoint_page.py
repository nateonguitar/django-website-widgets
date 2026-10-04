from website_widgets.example.advanced.pages.advanced_demo_page.advanced_demo_page import AdvancedDemoPage
from website_widgets.example.advanced.widgets.tip_card.tip_card import TipCard


class WidgetFromEndpointPage(AdvancedDemoPage):
    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Server-rendered widget from an endpoint'
        self.context.page['description'] = (
            'An endpoint renders a widget on the server and the page inserts its HTML.')
        self.context.children['first_tip'] = TipCard(number=0)
