import inspect
import os

from django.http import HttpRequest, HttpResponse
from django.utils.safestring import SafeText

from website_widgets.widget import Widget


class Page(Widget):
    """
    Base class for pages that render content within a base template.

    DEFAULT LIFECYCLE (no overrides):
    When .as_view() is called in urls.py, it returns a view function that:
    1. Creates a fresh page instance per request
    2. Sets self._request (accessible as self.request property)
    3. Calls init_page_state() - does nothing by default
    4. Calls set_context() - does nothing by default
    5. Calls html_sync() - renders the page's template.html
    6. Calls build_response() - wraps content in base template, returns HttpResponse

    LIFECYCLE HOOKS (in execution order):

    1. render_page(request, *args, **kwargs) -> HttpResponse
       - Entry point registered in urls.py
       - Orchestrates the entire page rendering flow
       - Override for complete control over lifecycle or exception handling
       - See the example app_page.py for common patterns
       - Most pages won't need to override this

    2. init_page_state(request, *args, **kwargs)
       - First hook called - for app-wide page state
       - By default: does nothing (request/user already set by .as_view())
       - Override in intermediate app classes (e.g., AppPage) to add:
         * Theme detection
         * Default page metadata (title, description)
         * App-wide widgets (header, footer, navigation)
         * Authentication/permission checks
       - Note: self.request and self.user are available
       - No need to call super() - base implementation is empty

    3. set_context(*args, **kwargs)
       - Second hook - sets page-specific context
       - By default: does nothing
       - Override in individual page classes to add:
         * Page-specific data (fetched from database, APIs, etc.)
         * Dynamic children widgets unique to this page
         * Context that varies based on URL parameters
       - Note: self.request and self.user are available
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
        path('my-page/', MyPage.as_view(), name='my_page')

        # The page's template.html renders main content, which gets injected
        # into the base template as {{ main_content_html }}.
    """

    status_code: int = 200

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Factory method that creates a fresh page instance per request.

        Returns an async view function compatible with Django URL patterns.
        Sets up request and user on the instance before calling render_page().

        Usage:
            path('my-page/', MyPage.as_view(), name='my_page')
        """
        async def view(request: HttpRequest, *args, **kwargs):
            instance = cls(**initkwargs)
            instance._request = request
            return await instance.render_page(request, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs
        return view

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
        Main entry point registered in urls.py via .as_view().

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

        Note: When using .as_view(), self.request is available throughout the lifecycle.
        Templates have direct access to {{ request }} and {{ user }} via Django context.
        """
        await self.init_page_state(request, *args, **kwargs)

        await self.set_context(*args, **kwargs)

        main_content_html = self.html_sync()

        return self.build_response(main_content_html)

    async def init_page_state(self, request: HttpRequest, *args, **kwargs):
        """
        Hook for app-wide context setup that runs before set_context().

        Override in intermediate app classes (e.g., AppPage) to add:
        - Theme detection
        - Default page values (title, meta description)
        - App-wide widgets (header, footer, navigation)
        - Authentication/permission checks

        Note: Base implementation is empty. No need to call super().
        """
        pass

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
