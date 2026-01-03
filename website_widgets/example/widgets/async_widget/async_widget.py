import asyncio
from django.utils.safestring import SafeText
from website_widgets import Widget


class AsyncWidget(Widget):
    """
    Example widget with async set_context() method.
    Demonstrates that the system auto-detects async vs sync.
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    async def set_context(self):
        # Simulate async operation (e.g., fetching data)
        await asyncio.sleep(0.01)
        self.context.data['message'] = self.message
        self.context.data['async_result'] = 'Fetched asynchronously'
