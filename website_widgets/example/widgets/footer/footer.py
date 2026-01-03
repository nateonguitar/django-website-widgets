from django.utils.safestring import SafeText

from website_widgets import Widget


class ExampleFooter(Widget):
    """Footer for the example app."""

    def html(self) -> SafeText:
        return self.render_html()
