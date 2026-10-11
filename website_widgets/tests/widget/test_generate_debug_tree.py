from website_widgets.tests.sample_widgets import DefaultTemplateWidget, SyncContextWidget
from website_widgets.tests.widget_test_case import WidgetTestCase


class GenerateDebugTreeTestCase(WidgetTestCase):
    def test_generate_debug_tree__shows_class_name_only__when_no_debug_label(self):
        widget = DefaultTemplateWidget()

        self.assertIn('>DefaultTemplateWidget<', widget._generate_debug_tree())

    def test_generate_debug_tree__shows_label_beside_class_name__when_debug_label_set(self):
        widget = DefaultTemplateWidget()
        widget._debug_label = 'Tab #7'

        self.assertIn('>DefaultTemplateWidget(Tab #7)<', widget._generate_debug_tree())

    def test_generate_debug_tree__labels_each_child__when_children_have_labels(self):
        child = SyncContextWidget()
        child._debug_label = 'first'
        widget = DefaultTemplateWidget()
        widget.context.children['single'] = child
        widget.context.children['many'] = [SyncContextWidget()]

        tree = widget._generate_debug_tree()

        self.assertIn('>SyncContextWidget(first)<', tree)
        self.assertIn('>SyncContextWidget<', tree)
