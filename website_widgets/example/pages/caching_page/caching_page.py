from datetime import datetime, timezone

from website_widgets.example.pages.app_page import ExampleAppPageComplex


class CachingPage(ExampleAppPageComplex):
    """
    Example page demonstrating ETag and Last-Modified caching.

    Uses ExampleAppPageComplex which provides:
    - ETag generation
    - Canonical URL generation
    - 304 Not Modified responses
    """

    # Simulated last modification time (in real app, from database)
    LAST_MODIFIED = datetime(2025, 12, 24, 12, 0, 0, tzinfo=timezone.utc)

    async def set_context(self, *args, **kwargs):
        self.context.page.set('title', 'Caching Example')
        self.context.page.set('show_parent_link', True)
        self.context.data.set('last_modified', self.LAST_MODIFIED.isoformat())

    async def get_last_modified(self, request, *args, **kwargs) -> datetime | None:
        """Return the last modified time to enable conditional requests."""
        return self.LAST_MODIFIED
