from website_widgets.tests.sample_widgets import DefaultTemplateWidget, SyncContextWidget
from website_widgets.tests.widget_test_case import WidgetTestCase


class GenerateDebugTreeTestCase(WidgetTestCase):
    def test_generate_debug_tree__shows_class_name_only__when_no_debug_label(self):
        widget = DefaultTemplateWidget()

        tree = widget._generate_debug_tree()

        self.assertIn('>DefaultTemplateWidget<', tree)

    def test_generate_debug_tree__shows_label_beside_class_name__when_debug_label_set(self):
        widget = DefaultTemplateWidget()
        widget.debug_label = 'Tab #7'

        tree = widget._generate_debug_tree()

        self.assertIn('>DefaultTemplateWidget(Tab #7)<', tree)

    def test_generate_debug_tree__labels_each_child__when_children_have_labels(self):
        labelled_child_widget = SyncContextWidget()
        labelled_child_widget.debug_label = 'first'
        listed_child_widget = SyncContextWidget()
        widget = DefaultTemplateWidget()
        widget.context.children['single'] = labelled_child_widget
        widget.context.children['many'] = [listed_child_widget]

        tree = widget._generate_debug_tree()

        self.assertIn('>SyncContextWidget(first)<', tree)
        self.assertIn('>SyncContextWidget<', tree)
