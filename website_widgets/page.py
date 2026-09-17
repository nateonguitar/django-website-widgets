from django.http import HttpRequest, HttpResponse
from django.utils.safestring import SafeText, mark_safe
from django.conf import settings
import inspect

from website_widgets.widget import Widget
from website_widgets.config import get_config


class Page(Widget):
    """
    Base class for pages that render content within a base template.

    DEFAULT LIFECYCLE (no overrides):
    When .as_view() is called in urls.py, it returns a view function that:
    1. Creates a fresh page instance per request
    2. Sets self._request (accessible as self.request property)
    3. Calls handle_request()
       - Calls set_context() - override to set page data/children
       - Calls build_response() - automatically renders everything
    4. Returns HttpResponse

    LIFECYCLE HOOKS (in execution order):

    1. handle_request(request, *args, **kwargs) -> HttpResponse
       - Entry point registered in urls.py (can be sync or async)
       - Orchestrates the entire page rendering flow
       - Override for complete control over lifecycle or exception handling
       - Default: calls set_context() then build_response()

    2. set_context(*args, **kwargs)
       - Main hook for setting up page context and state
       - Can be sync (def) or async (async def) - system auto-detects
       - Override in app base classes (e.g., AppPage) to add:
         * Theme detection
         * Default page metadata (title, description)
         * App-wide widgets (header, footer, navigation)
         * Authentication/permission checks
       - Override in individual page classes to add:
         * Page-specific data (fetched from database, APIs, etc.)
         * Dynamic children widgets unique to this page
         * Context that varies based on URL parameters
       - Pattern: Call super().set_context() first

    3. build_response() -> HttpResponse
       - Creates the final HttpResponse
       - Automatically handles:
         * Debug tree capture
         * Widget tree initialization (calls set_context on all children)
         * Rendering all widgets to HTML
         * Wrapping content in base template
       - Override to customize response headers or status codes
       - Call await super().build_response() to get response, then modify

    REQUIRED IMPLEMENTATION:
    - base_template_path(): Return path to the base template that wraps content

    USAGE:
        # In urls.py:
        path('my-page/', MyPage.as_view(), name='my_page')

        # The page's own template renders main content, which gets injected
        # into the base template as {{ main_content_html }}.
    """

    status_code: int = 200

    @classmethod
    def as_view(cls, *initargs, **initkwargs):
        """
        Factory method that creates a fresh page instance per request.

        Returns an async view function compatible with Django URL patterns.
        Sets up request and user on the instance before calling handle_request().

        URL parameters are passed to both the constructor and handle_request().
        This allows pages to store URL parameters as instance attributes.

        Usage:
            path('my-page/', MyPage.as_view(), name='my_page')
            path('profile/<str:username>/', ProfilePage.as_view(), name='profile')
        """
        async def view(request: HttpRequest, *args, **kwargs):
            instance = cls(*args, *initargs, **kwargs, **initkwargs)
            instance._request = request

            # Call handle_request (can be sync or async)
            if inspect.iscoroutinefunction(instance.handle_request):
                return await instance.handle_request(request, *args, **kwargs)
            else:
                return instance.handle_request(request, *args, **kwargs)

        view.view_class = cls
        view.view_initargs = initargs
        view.view_initkwargs = initkwargs
        return view

    def html(self) -> SafeText:
        """Render the page's main content template."""
        return self.render_html()

    def base_template_path(self) -> str:
        """
        Return the path to the base template that wraps this page's content.

        Override this in subclasses to specify which base template to use.
        Common pattern: create an intermediate class that sets a default,
        then individual pages can override if needed.
        """
        raise NotImplementedError("Subclasses must implement `base_template_path()`.")

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Main entry point registered in urls.py via .as_view().

        Can be sync (def) or async (async def) - system auto-detects.

        Override this method for:
        - Exception handling (UnauthorizedException, RedirectException, etc.)
        - Conditional responses (304 Not Modified with ETags)
        - Custom headers (Content-Security-Policy, Cache-Control)
        - Early returns based on request conditions
        - Custom flow control or logging

        Alternatively, override the individual lifecycle hooks:
        - set_context(): App-wide and page-specific context
        - build_response(): Customize the response

        Default implementation:
        ```python
            # Call set_context (sync or async)
            if inspect.iscoroutinefunction(self.set_context):
                await self.set_context()
            else:
                self.set_context()

            # Build and return response (automatic rendering)
            return await self.build_response()
        ```

        Example pattern for exception handling:
        ```python
            try:
                if inspect.iscoroutinefunction(self.set_context):
                    await self.set_context()
                else:
                    self.set_context()
                return await self.build_response()
            except ExampleNotAuthorizedException as e:
                return self.build_not_authorized_response(e)
            except ExampleRedirectException as e:
                return self.build_redirect_response(e)
        ```
        """
        # Call set_context (can be sync or async)
        if inspect.iscoroutinefunction(self.set_context):
            await self.set_context()
        else:
            self.set_context()

        return await self.build_response()

    async def build_response(self) -> HttpResponse:
        """
        Creates the final HttpResponse with the rendered page content.

        Automatically handles:
        - Capturing debug tree (before rendering)
        - Rendering children widgets to HTML
        - Rendering main content (calls self.html())
        - Wrapping content in base template
        - Appending debug tree if enabled

        Override to customize response headers, status codes, or add additional processing.
        Call await super().build_response() to get the response, then modify it.
        """
        # Initialize the entire widget tree (call set_context on all widgets)
        await self._initialize_widget_tree()

        # Capture debug tree AFTER initializing (so all children are populated)
        self._debug_tree_html = None
        if get_config().show_debug_tree:
            self._debug_tree_html = self._generate_debug_tree()

        # Render children to HTML
        await self._render_children_to_html()

        # Render main content (or use override if set)
        if hasattr(self, '_override_main_content_html'):
            main_content_html = self._override_main_content_html
        else:
            main_content_html = self.html()

        # Append debug widget tree if it was captured
        if hasattr(self, '_debug_tree_html') and self._debug_tree_html:
            debug_tree_html = f"""
            <div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-top: 2px solid #ddd; font-family: monospace; font-size: 14px; box-sizing: border-box; width: 100%; max-width: 100%;">
                <h3 style="margin-top: 0; color: #333;">Widget Tree Debug View</h3>
                <div style="background: white; padding: 15px; border-radius: 4px; border: 1px solid #ddd; overflow-x: auto; word-wrap: break-word; box-sizing: border-box;">
                    {self._debug_tree_html}
                </div>
            </div>
            <style>
                @media (max-width: 768px) {{
                    div[style*="Widget Tree Debug"] {{
                        padding: 12px !important;
                        font-size: 12px !important;
                    }}
                }}
            </style>
            """
            main_content_html = main_content_html + mark_safe(debug_tree_html)

        html = self.render_html(
            template_path=self.base_template_path(),
            extra_context={
                'main_content_html': main_content_html,
            })
        return HttpResponse(html, status=self.status_code)
