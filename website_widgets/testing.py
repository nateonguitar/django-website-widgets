"""
What the package offers a project's tests. Imported on its own,
`from website_widgets.testing import WidgetDocumentTestMixin`, so production never loads it.
"""

from __future__ import annotations

from django.utils.safestring import SafeText

from website_widgets.widget import AsyncWidget, SyncWidget


class _TestDocument(SyncWidget):
    """
    The document `WidgetDocumentTestMixin` renders: its template is the test's, its children the
    widget under test and the document's own.
    """

    def __init__(self, template_string: str, children: dict):
        super().__init__()
        self.template_string = template_string
        self.children = children

    def set_context(self):
        self.context.children.update(self.children)


class WidgetDocumentTestMixin:
    """
    Renders one widget into a small HTML document a test controls, instead of the whole page that
    would hold it, so a test gets the widget and only the chrome it asks for.

    A mixin, combined with whichever Django test class the test already uses:

        class MovieCardTests(WidgetDocumentTestMixin, TestCase):
            def test_title__shows__when_rendered(self):
                html = self.render_document(MovieCard(movie))

    The document is itself a widget whose template is `document_template`. Its children are
    `document_children()` (merged with the call's `document_children`) plus the widget under
    test under the key `widget`, so the template places `{{ children.widget }}` and any other
    child, such as `{{ children.appbar }}`. `page_context(user)` (merged with the call's
    `page_context`) fills `context.page` for the whole tree, as a page would; the document is
    the root, so values set on the widget's own `context.page` beforehand raise instead.

    The same HTML serves a JS test (loaded into a fake DOM) and a browser test (opened in a
    browser), so a subclass's `document_template` is where a project adds its CSS bundle, fonts
    or a CDN script, in `<head>` with `{% static %}`.
    """

    document_template: str = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '</head>\n'
        '<body>\n'
        '{{ children.widget }}\n'
        '</body>\n'
        '</html>\n'
    )

    # The key the widget under test is placed under in the document's children.
    DOCUMENT_WIDGET_KEY = 'widget'

    def document_children(self) -> dict:
        """Children every document in this test class holds beside the widget, such as an appbar. Override."""
        return {}

    def page_context(self, user) -> dict:
        """
        `context.page` values every render in this test class starts with, such as what a
        project's page base puts there before any widget runs. `user` is the one the render was
        given (or `None`), for a project whose widgets read the user from `context.page`. Override.
        """
        return {}

    def render_document(
        self,
        widget: SyncWidget,
        user=None,
        document_children: dict | None = None,
        page_context: dict | None = None,
    ) -> SafeText:
        """
        The widget inside `document_template`, rendered with `render__test()` against a mock
        `GET /` whose `request.user` is `user`. Sync, so every widget in the tree must be a
        `SyncWidget`; await `arender_document()` for an `AsyncWidget`.
        """
        document = self._build_document(widget, user, document_children, page_context)
        return document.render__test(user=user)

    async def arender_document(
        self,
        widget: AsyncWidget | SyncWidget,
        user=None,
        document_children: dict | None = None,
        page_context: dict | None = None,
    ) -> SafeText:
        """`render_document()` for async tests, through `arender__test()`, so the tree may hold either kind of widget."""
        document = self._build_document(widget, user, document_children, page_context)
        return await document.arender__test(user=user)

    def _build_document(
        self,
        widget: AsyncWidget | SyncWidget,
        user,
        document_children: dict | None,
        page_context: dict | None,
    ) -> _TestDocument:
        # Copies, so a hook returning a shared dict is never written into.
        children = dict(self.document_children())
        if document_children is not None:
            children.update(document_children)
        if self.DOCUMENT_WIDGET_KEY in children:
            raise ValueError(
                f"A document child is named '{self.DOCUMENT_WIDGET_KEY}', the key the widget under "
                f"test is placed under; rename that child.")
        children[self.DOCUMENT_WIDGET_KEY] = widget

        page = dict(self.page_context(user))
        if page_context is not None:
            page.update(page_context)

        document = _TestDocument(self.document_template, children)
        document.context.page.update(page)
        return document
