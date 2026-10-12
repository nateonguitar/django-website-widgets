from website_widgets import Widget


class SiteHeader(Widget):
    """
    The site name and who is logged in, from `context.page`. A child of every page, rendered by
    the document template, so it sits outside the page's own content.
    """
