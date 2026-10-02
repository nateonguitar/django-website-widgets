from django.urls import reverse
from website_widgets.example.pages.page_superclasses import ExamplePageSimple
from website_widgets.example.widgets.footer.footer import ExampleFooter


class ExampleIndexPage(ExamplePageSimple):
    """
    Index page listing all available example.
    """

    def set_context(self):
        super().set_context()

        # The Simple super class does not add appbar/footer automatically.
        # The super class uses base.html will try to render both the header and footer,
        # but django's template engine will just ignore missing context children.
        # Only adding the footer to demonstrate, as the appbar is not needed on index page.
        self.context.children['footer'] = ExampleFooter()

        self.context.page['title'] = 'Example'
        self.context.data['example_pages'] = [
            {
                'name': 'Simple Page',
                'url': reverse('example_simple_page'),
                'description': 'Minimal page using ExamplePageSimple.',
            },
            {
                'name': 'Widget Composition',
                'url': reverse('example_widget_composition_page'),
                'description': 'Demonstrates child widgets with explicit data passing.',
            },
            {
                'name': 'URL Parameters',
                'url': reverse('example_profile', kwargs={'username': 'django_dev'}),
                'description': 'Page with URL path parameters passed to constructor.',
            },
            {
                'name': 'Unwrapped Page',
                'url': reverse('example_unwrapped_page'),
                'description': 'Sets base_template_path for pages without the app shell.',
            },
            {
                'name': 'HTTP Caching',
                'url': reverse('example_caching_page'),
                'description': 'Uses ExamplePageComplex with ETag, Last-Modified, and canonical URLs.',
            },
        ]
