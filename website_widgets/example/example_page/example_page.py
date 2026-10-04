import os

from website_widgets import Page, Widget


class ExamplePage(Page):
    """
    The root of every example page: the `<head>` values and a stylesheet.

    Each of the example's apps (the index, the projects app, the advanced demo) has a base page
    that subclasses this and sets its own `stylesheet_class`, so each app looks different. The
    projects app also brings its own layout.
    """

    # Absolute, since the pages using it sit at different depths.
    base_template_path = os.path.join(os.path.dirname(__file__), 'example_layout.html')
    SITE_NAME = 'website_widgets example'

    stylesheet_class: type[Widget]

    def set_context(self):
        self.context.page['site_name'] = self.SITE_NAME
        self.context.page['title'] = self.SITE_NAME
        self.context.page['description'] = 'A small demo site built with django-website-widgets.'
        self.context.children['stylesheet'] = self.stylesheet_class()
