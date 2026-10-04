from django.urls import reverse

from website_widgets.example.example_page.example_page import ExamplePage
from website_widgets.example.index.widgets.index_stylesheet.index_stylesheet import IndexStylesheet


class IndexPage(ExamplePage):
    stylesheet_class = IndexStylesheet

    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Examples'
        self.context.page['description'] = (
            'What django-website-widgets does: server-rendered pages with JavaScript on top.')
        self.context.data['apps'] = [
            {
                'name': 'Projects app',
                'url': reverse('website_widgets_example_projects'),
                'description': (
                    'A small project tracker with a fake login: an appbar, access-denied and '
                    'not-found variants, and creating, editing and deleting through JSON endpoints.'),
            },
            {
                'name': 'Advanced functionality demo',
                'url': reverse('website_widgets_example_advanced'),
                'description': (
                    'The mechanics on their own: composition, async widgets, a widget rendered by an '
                    'endpoint, and a conditional (304) response.'),
            },
        ]
