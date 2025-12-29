from datetime import datetime, timezone

from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.pages.page_superclasses import ExamplePageComplex


class CachingPage(ExamplePageComplex):
    """
    Example page demonstrating ETag and Last-Modified caching.

    Uses ExamplePageComplex which provides:
    - ETag generation
    - Canonical URL generation
    - 304 Not Modified responses
    """

    # Simulated last modification time (in real app, from database)
    LAST_MODIFIED = datetime(2025, 12, 24, 12, 0, 0, tzinfo=timezone.utc)

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        self.context.page['title'] = 'Caching Example'
        self.context.page['show_appbar_back_button'] = True
        self.context.page['nav_item'] = NavItem.CACHING_PAGE
        self.context.data['last_modified'] = self.LAST_MODIFIED.isoformat()

    async def get_last_modified(self, request, *args, **kwargs) -> datetime | None:
        """Return the last modified time to enable conditional requests."""
        return self.LAST_MODIFIED
