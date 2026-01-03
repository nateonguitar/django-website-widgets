import asyncio
from django.utils.safestring import SafeText
from website_widgets import Widget


class AsyncWidget(Widget):
    """
    Example widget with async html() method.
    Demonstrates that the system auto-detects async vs sync.
    """

    def __init__(self, message: str, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self.message = message

    async def html(self) -> SafeText:
        # Simulate async operation (e.g., fetching data)
        await asyncio.sleep(0.01)
        self.context.data['message'] = self.message
        self.context.data['async_result'] = 'Fetched asynchronously'
        return self.render_html()
