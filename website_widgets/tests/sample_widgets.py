"""
Widgets and pages the tests render. A widget's template is looked up beside the module its class
is defined in, so every template a test writes goes beside this one, through
`WidgetTestCase.write_template()`.
"""

import asyncio
import os

from website_widgets.page import Page
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


class UnsetDocumentPage(Page):
    pass


class ClassLevelDocumentPage(Page):
    document_template_path = '../templates/document_template.html'


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
