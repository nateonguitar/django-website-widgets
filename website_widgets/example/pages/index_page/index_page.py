from website_widgets.example.pages.app_page import ExampleAppPageSimple


class ExampleIndexPage(ExampleAppPageSimple):
    """
    Index page listing all available example.
    """

    async def set_context(self, *args, **kwargs):

        self.context.page['title'] = 'example'
        self.context.data['example'] = [
            {
                'name': 'Simple Page',
                'url': '/example/simple/',
                'description': 'Minimal page using ExampleAppPageSimple.',
            },
            {
                'name': 'Widget Composition',
                'url': '/example/widget-composition/',
                'description': 'Demonstrates child widgets with explicit data passing.',
            },
            {
                'name': 'Unwrapped Page',
                'url': '/example/unwrapped/',
                'description': 'Override base_template_path() for pages without the app shell.',
            },
            {
                'name': 'HTTP Caching',
                'url': '/example/caching/',
                'description': 'Uses ExampleAppPageComplex with ETag, Last-Modified, and canonical URLs.',
            },
        ]
