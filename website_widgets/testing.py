"""
What the package offers a project's tests. Imported on its own,
`from website_widgets.testing import WidgetDocumentTestMixin`, so production never loads it.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import unittest

from django.core.management.base import CommandError
from django.test.runner import DiscoverRunner, ParallelTestSuite
from django.utils.module_loading import import_string
from django.utils.safestring import SafeText

from website_widgets.config import get_config
from website_widgets.management.website_app import WebsiteApp
from website_widgets.widget import AsyncWidget, SyncWidget

try:
    import tblib
except ImportError:
    tblib = None


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


class WebsiteWidgetsParallelTestSuite(ParallelTestSuite):
    """Starts the runner's `patches()` in each `--parallel` worker, which has no runner of its own."""

    # Django pickles this function by its qualified name and calls it first in each worker with
    # `process_setup_args`, which the runner sets to its own dotted path.
    def process_setup(runner_path):
        runner_class = import_string(runner_path)
        runner_class.start_patches()


class WebsiteWidgetsTestRunner(DiscoverRunner):
    """
    Django's runner, plus: a run holding browser tests (tagged `TestingConfig.browser_test_tag`)
    builds the frontend first, and a subclass's `patches()` cover every test, in `--parallel`
    workers too. `TEST_RUNNER = 'website_widgets.testing.WebsiteWidgetsTestRunner'`.
    """

    parallel_test_suite = WebsiteWidgetsParallelTestSuite

    # The patchers `start_patches()` started in this process, so the main process can stop them.
    _started_patchers: list = []

    def __init__(self, no_build: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.no_build = no_build

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--no-build',
            action='store_true',
            help='Run browser tests against the last frontend build instead of building first.')

    @classmethod
    def patches(cls) -> list:
        """
        Override: `unittest.mock.patch(...)` objects, not started, that every test in the run
        runs under, such as one replacing an SMS provider's client. Started in the main process
        and in each `--parallel` worker, which a patch started anywhere else never reaches.
        """
        return []

    @classmethod
    def start_patches(cls):
        cls._started_patchers = cls.patches()
        for patcher in cls._started_patchers:
            patcher.start()

    @classmethod
    def stop_patches(cls):
        for patcher in reversed(cls._started_patchers):
            patcher.stop()
        cls._started_patchers = []

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.start_patches()

    def teardown_test_environment(self, **kwargs):
        self.stop_patches()
        super().teardown_test_environment(**kwargs)

    def build_suite(self, test_labels=None, **kwargs):
        suite = super().build_suite(test_labels, **kwargs)
        if isinstance(suite, ParallelTestSuite):
            runner_class = type(self)
            suite.process_setup_args = (f'{runner_class.__module__}.{runner_class.__qualname__}',)
            if tblib is None:
                self.log(
                    'tblib is not installed, so a test failing in a --parallel worker ends the run '
                    'without its traceback: add tblib as a dev dependency.',
                    level=logging.WARNING)
        if self.has_browser_tests(suite):
            self.build_frontend()
        return suite

    @staticmethod
    def has_browser_tests(suite: unittest.TestSuite) -> bool:
        """Whether the suite, after --tag and --exclude-tag, holds a test carrying the browser tag."""
        browser_test_tag = get_config().testing.browser_test_tag
        # A parallel suite keeps its tests in subsuites, one per test case class.
        suites = suite.subsuites if isinstance(suite, ParallelTestSuite) else [suite]
        pending = list(suites)
        while pending:
            item = pending.pop()
            if isinstance(item, unittest.TestSuite):
                pending.extend(item)
                continue
            test_method = getattr(item, getattr(item, '_testMethodName', ''), None)
            tags = set(getattr(item, 'tags', ())) | set(getattr(test_method, 'tags', ()))
            if browser_test_tag in tags:
                return True
        return False

    def build_frontend(self):
        """Runs `TestingConfig.build_command` in the website app's folder, raising CommandError when it can't or it fails."""
        command = get_config().testing.build_command
        if command is None or self.no_build:
            return
        website_app = WebsiteApp.from_config()
        if website_app.scripts is None:
            # No package.json, so no frontend to build.
            return
        problem = website_app.build_problem(command)
        if problem is not None:
            raise CommandError(f'The browser tests need the frontend built, but {problem}.')
        command_line = ' '.join(command)
        self.log(f'Building the frontend for the browser tests: {command_line} (in {website_app.shown_folder})')
        # The build's output goes straight to the terminal, so this line must be there first.
        sys.stdout.flush()
        # The full path, which Windows needs for npm's .cmd shim without a shell.
        executable = shutil.which(command[0])
        completed = subprocess.run([executable, *command[1:]], cwd=website_app.folder)
        if completed.returncode != 0:
            raise CommandError(
                f'The frontend build, {command_line}, failed, so no test ran. --no-build runs them '
                f'against the last build.')
