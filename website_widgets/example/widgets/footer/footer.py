from django.utils.safestring import SafeText

from website_widgets import Widget


class ExampleFooter(Widget):
    """Footer for the example app."""

    def html_sync(self) -> SafeText:
        return self.render_html(self.template_path())
