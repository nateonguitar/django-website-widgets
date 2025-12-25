import inspect
import os

from django.http import HttpRequest, HttpResponse
from django.utils.safestring import SafeText

from website_widgets.widget import Widget


class Page(Widget):
    """
    Base class for pages that render content within a base template.

    DEFAULT LIFECYCLE (no overrides):
    When render_page() is called, the following happens automatically:
    1. init_page_state() runs - sets up request/user in context
    2. set_context() runs - does nothing by default
    3. html_sync() runs - renders the page's template.html
    4. build_response() runs - wraps content in base template, returns HttpResponse

    LIFECYCLE HOOKS (in execution order):

    1. render_page(request, *args, **kwargs) -> HttpResponse
       - Entry point registered in urls.py
       - Orchestrates the entire page rendering flow
       - Override for complete control over lifecycle or exception handling
       - See the example app_page.py for common patterns
       - Most pages won't need to override this

    2. init_page_state(request, *args, **kwargs)
       - First hook called - sets up app-wide page state
       - By default: stores request and user in page context
       - Override in intermediate app classes (e.g., AppPage) to add:
         * Theme detection
         * Default page metadata (title, description)
         * App-wide widgets (header, footer, navigation)
         * Authentication/permission checks
       - MUST call super().init_page_state() first to maintain the request chain

    3. set_context(*args, **kwargs)
       - Second hook - sets page-specific context
       - By default: does nothing
       - Override in individual page classes to add:
         * Page-specific data (fetched from database, APIs, etc.)
         * Dynamic children widgets unique to this page
         * Context that varies based on URL parameters
       - This is where most page-specific logic goes

    4. html_sync() -> SafeText
       - Renders the page's template.html into HTML
       - Uses context built by init_page_state() and set_context()
       - Rarely needs to be overridden

    5. build_response(main_content_html) -> HttpResponse
       - Creates the final HttpResponse
       - Wraps main content in base template
       - Rarely needs to be overridden
       - Note: Set self.status_code anywhere before this to control status
       - Note: Can add headers to response after it's built in render_page()

    REQUIRED IMPLEMENTATION:
    - base_template_path(): Return path to the base template that wraps content

    USAGE:
        # In urls.py:
        path('my-page/', MyPage().render_page, name='my_page')

        # The page's template.html renders main content, which gets injected
        # into the base template as {{ main_content_html }}.
    """

    status_code: int = 200

    def html_sync(self) -> SafeText:
        """Render the page's main content template."""
        return self.render_html(self.template_path())

    async def html(self) -> SafeText:
        """Pages use html_sync() since async work is done in set_context()."""
        raise NotImplementedError(
            f"{self.__class__.__name__} is a page - use html_sync() instead. "
            "All async work should be done in set_context().")

    def folder_path(self) -> str:
        """
        Return the directory path containing this page's template.html.
        Auto-detected from the subclass file location. Override if needed.
        """
        return os.path.dirname(inspect.getfile(self.__class__))

    def base_template_path(self) -> str:
        """
        Return the path to the base template that wraps this page's content.

        Override this in subclasses to specify which base template to use.
        Common pattern: create an intermediate class (e.g., AppPage)
        that sets a default, then individual pages can override if needed.
        """
        raise NotImplementedError("Subclasses must implement `base_template_path()`.")

    async def render_page(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Main entry point registered in urls.py.

        Override this method for:
        - Exception handling (UnauthorizedException, RedirectException, etc.)
        - Conditional responses (304 Not Modified with ETags)
        - Custom headers (Content-Security-Policy, Cache-Control)
        - Early returns based on request conditions
        - Custom flow control or logging

        Alternatively, override the individual lifecycle hooks:
        - init_page_state(): App-wide setup before set_context
        - set_context(): Page-specific context
        - build_response(): Customize the response

        When overriding render_page(), call super().init_page_state(request, *args, **kwargs)
        to ensure self.request and self.user are available throughout the lifecycle.
        This also makes {{ request }} and {{ user }} accessible in all templates.
        """
        self._init_page_state_called = False

        await self.init_page_state(request, *args, **kwargs)

        if not self._init_page_state_called:
            raise RuntimeError(
                f"{self.__class__.__name__}.init_page_state() must call "
                "super().init_page_state(request, *args, **kwargs) first."
            )

        await self.set_context(*args, **kwargs)

        main_content_html = self.html_sync()

        return self.build_response(main_content_html)

    async def init_page_state(self, request: HttpRequest, *args, **kwargs):
        """
        Override to add app-wide context that runs before set_context().

        IMPORTANT: Subclasses must call super().init_page_state(request, *args, **kwargs)
        as the first line of their override.

        Use for page-level setup such as:
        - Theme detection
        - Default page values (title, meta description)
        - Selected navigation item
        """
        self._request = request
        self.context.page.set('request', request)
        self.context.page.set('user', request.user)
        self._init_page_state_called = True

    async def set_context(self, *args, **kwargs):
        """
        Override to set page-specific context.
        Runs after init_page_state().
        """
        pass

    def build_response(self, main_content_html: str) -> HttpResponse:
        html = self.render_html(
            template_path=self.base_template_path(),
            context={
                'main_content_html': main_content_html,
            })
        return HttpResponse(html, status=self.status_code)
