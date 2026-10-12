import os

from django.urls import reverse

from website_widgets import Page


class ExamplePage(Page):
    """
    The base of every page here: the shared document template and the `<head>` values. It has no
    `@register_url`, so route discovery leaves it unrouted, as a base class should be.
    """

    # Absolute: a relative path resolves beside each page's own module, not this one.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')
    SITE_NAME = 'Pages and widgets'

    # Left unset, the tab shows only the site's name, as the home page's does.
    page_title: str | None = None
    page_description = 'django-website-widgets example: pages, widgets and how data reaches them.'

    def set_context(self):
        self.context.page['site_name'] = self.SITE_NAME
        self.context.page['title'] = self.page_title
        self.context.page['description'] = self.page_description
        self.context.page['index_url'] = reverse('website:IndexPage')
