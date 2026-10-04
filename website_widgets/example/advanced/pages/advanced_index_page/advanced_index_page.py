from django.urls import reverse

from website_widgets.example.advanced.pages.advanced_demo_page.advanced_demo_page import AdvancedDemoPage


class AdvancedIndexPage(AdvancedDemoPage):
    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Advanced demo'
        self.context.page['description'] = (
            'How widgets compose, async widgets, widgets rendered by an endpoint, and conditional '
            'responses.')
        self.context.page['back_url'] = reverse('website_widgets_example_index')
        self.context.page['back_label'] = 'All examples'
        self.context.data['demos'] = [
            {
                'name': 'Composition',
                'url': reverse('website_widgets_example_composition'),
                'description': (
                    'Data passed down through constructors, the shared page context, list children '
                    'and a skipped child.'),
            },
            {
                'name': 'Async widgets',
                'url': reverse('website_widgets_example_async'),
                'description': (
                    'Awaiting in set_context(): widgets that each await their own query run one '
                    'after another, while a parent can run them together and pass the results down.'),
            },
            {
                'name': 'Server-rendered widget from an endpoint',
                'url': reverse('website_widgets_example_widget_from_endpoint'),
                'description': (
                    'A widget rendered with the page, and a button that asks an endpoint for another, '
                    'rendered on the server, to add under it.'),
            },
            {
                'name': 'Conditional response',
                'url': reverse('website_widgets_example_conditional'),
                'description': 'An ETag, and a 304 Not Modified when the browser already has the page.',
            },
        ]
