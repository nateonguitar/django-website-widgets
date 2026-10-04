from django.urls import reverse

from website_widgets.example.advanced.widgets.advanced_stylesheet.advanced_stylesheet import AdvancedStylesheet
from website_widgets.example.example_page.example_page import ExamplePage


class AdvancedDemoPage(ExamplePage):
    """The advanced demo's base page: its stylesheet and a link back to the demo's index."""

    stylesheet_class = AdvancedStylesheet

    def set_context(self):
        super().set_context()
        self.context.page['back_url'] = reverse('website_widgets_example_advanced')
        self.context.page['back_label'] = 'Advanced demo'
