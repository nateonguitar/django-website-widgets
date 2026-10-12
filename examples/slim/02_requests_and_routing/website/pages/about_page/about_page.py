from website.pages.site_page import SitePage


class AboutPage(SitePage):
    """
    Routed by hand in `example_site/urls.py` with `AboutPage.as_view()`, like any Django view, so it
    has no `@register_url` and its name is plain `about`, outside the `website:` namespace.
    Discovery imports this module too, but only a decorated page is routed.
    """

    page_title = 'About'
