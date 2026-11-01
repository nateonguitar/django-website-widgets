"""
Widgets and pages the tests render. A widget's template is looked up beside the module its class
is defined in, so every template a test writes goes beside this one, through
`WidgetTestCase.write_template()`.
"""

import asyncio
import os

from website_widgets.web_page import AsyncWebPage, SyncWebPage
from website_widgets.widget import Widget


SAMPLE_WIDGETS_DIR = os.path.dirname(os.path.abspath(__file__))


class DefaultTemplateWidget(Widget):
    pass


class ClassLevelTemplateWidget(Widget):
    # An existing file stands in for a template, since only the lookup is tested.
    template_filename = 'sample_widgets.py'


class ContextChosenTemplateWidget(Widget):
    def set_context(self):
        self.template_filename = '__init__.py'


class BaseFolderWidget(Widget):
    pass


class SubfolderWidget(BaseFolderWidget):
    pass


class UnsetDocumentPage(AsyncWebPage):
    pass


class ClassLevelDocumentPage(AsyncWebPage):
    document_template_path = '../templates/document_template.html'


class DocumentPage(AsyncWebPage):
    """A page whose test sets both its templates, with a child for its own template to place."""

    def __init__(self, document_template_filename: str, template_filename: str, child_template_filename: str):
        super().__init__()
        self.document_template_path = document_template_filename
        self.template_filename = template_filename
        self.child_template_filename = child_template_filename

    async def set_context(self):
        self.context.data['word'] = 'async'
        self.context.children['child'] = WordWidget('child', self.child_template_filename)


class SyncDocumentPage(SyncWebPage):
    """`DocumentPage` as a SyncWebPage, whose child the test may make async."""

    def __init__(self, document_template_filename: str, template_filename: str, child: Widget):
        super().__init__()
        self.document_template_path = document_template_filename
        self.template_filename = template_filename
        self.child = child

    def set_context(self):
        self.context.data['word'] = 'sync'
        self.context.children['child'] = self.child


class SyncContextWidget(Widget):
    def set_context(self):
        self.context.data['word'] = 'sync'


class AsyncContextWidget(Widget):
    async def set_context(self):
        self.context.data['word'] = 'async'


class WordWidget(Widget):
    def __init__(self, word: str, template_filename: str):
        super().__init__()
        self.word = word
        self.template_filename = template_filename

    def set_context(self):
        self.context.data['word'] = self.word


class ParentWidget(Widget):
    def __init__(self, child_template_filename: str):
        super().__init__()
        self.child_template_filename = child_template_filename

    def set_context(self):
        self.context.children['single'] = WordWidget('one', self.child_template_filename)
        self.context.children['many'] = [
            WordWidget('two', self.child_template_filename),
            WordWidget('three', self.child_template_filename),
        ]
        self.context.children['absent'] = None


class RequestReadingWidget(Widget):
    def set_context(self):
        self.context.data['path'] = self.request.path


class LoopCheckingWidget(Widget):
    def set_context(self):
        try:
            asyncio.get_running_loop()
            self.context.data['loop'] = 'running'
        except RuntimeError:
            self.context.data['loop'] = 'none'


class AsyncChildParentWidget(Widget):
    def __init__(self, child_template_filename: str):
        super().__init__()
        self.child_template_filename = child_template_filename

    def set_context(self):
        child = AsyncContextWidget()
        child.template_filename = self.child_template_filename
        self.context.children['child'] = child


class HolderWidget(Widget):
    """Runs the test's `fill(children)` in set_context(), to place children any way a test needs."""

    def __init__(self, fill):
        super().__init__()
        self.fill = fill

    def set_context(self):
        self.fill(self.context.children)


class EarlyPageWritingWidget(Widget):
    """Writes context.page in its constructor, before a parent shares the page's dict with it."""

    def __init__(self):
        super().__init__()
        self.context.page['early'] = 'lost'


class RequestInConstructorWidget(Widget):
    def __init__(self):
        super().__init__()
        self.path = self.request.path


class RequestInConstructorPage(AsyncWebPage):
    def __init__(self):
        super().__init__()
        self.path = self.request.path


class PageValueWidget(Widget):
    """Writes `page[key] = value` in set_context(), for its siblings and parent to read."""

    def __init__(self, key: str, value: str, template_filename: str):
        super().__init__()
        self.key = key
        self.value = value
        self.template_filename = template_filename

    def set_context(self):
        self.context.page[self.key] = self.value


class PageWritingPage(AsyncWebPage):
    """
    Writes `context.page` in `handle_request()` before `set_context()`, as a project's AppPage
    puts the user there, and again in `set_context()`, with a child that reads both.
    """

    def __init__(self, document_template_filename: str, template_filename: str, child_template_filename: str):
        super().__init__()
        self.document_template_path = document_template_filename
        self.template_filename = template_filename
        self.child_template_filename = child_template_filename

    async def handle_request(self, request, *args, **kwargs):
        self.context.page['user'] = 'ann'
        return await super().handle_request(request, *args, **kwargs)

    async def set_context(self):
        self.context.page['title'] = 'Home'
        child = DefaultTemplateWidget()
        child.template_filename = self.child_template_filename
        self.context.children['child'] = child
