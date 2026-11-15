from django.test import RequestFactory

from website_widgets.tests.sample_widgets import (
    FileOverStringWidget,
    StringInheritingWidget,
    StringOverFileWidget,
    StringTemplatePage,
    StringTemplateWidget,
    VariantSwitchingStringWidget,
)
from website_widgets.tests.widget_test_case import WidgetTestCase
from website_widgets.widget import SyncWidget


class GetTemplateTestCase(WidgetTestCase):
    def test_get_template__renders_template_string__when_set_on_class(self):
        widget = StringTemplateWidget()

        html = widget.render()

        self.assertEqual(html, 'string template')

    async def test_get_template__renders_page_body_from_template_string__when_set_on_page(self):
        document_filename = self.write_template('<body>{{ page_content_html }}</body>')
        page = StringTemplatePage(document_filename)
        request = RequestFactory().get('/')
        page._request = request

        response = await page.handle_request(request)

        html = response.content.decode()
        self.assertEqual(html, '<body>page body</body>')

    def test_get_template__fails__when_one_class_sets_both(self):
        with self.assertRaises(TypeError) as caught:
            class BothWidget(SyncWidget):
                template_string = 'string'
                template_filename = 'file.html'

        message = str(caught.exception)
        self.assertIn('BothWidget', message)

    def test_get_template__renders_variant_file__when_template_filename_assigned_at_runtime(self):
        variant_filename = self.write_template('variant {{ data.word }}')
        widget = VariantSwitchingStringWidget(variant_filename)

        html = widget.render()

        self.assertEqual(html, 'variant template')

    def test_get_template__renders_template_string__when_no_variant_assigned(self):
        widget = VariantSwitchingStringWidget(None)

        html = widget.render()

        self.assertEqual(html, 'string template')

    def test_get_template__renders_subclass_file__when_base_sets_template_string(self):
        widget = FileOverStringWidget()

        html = widget.render()

        self.assertIn('Widgets and pages the tests render', html)

    def test_get_template__renders_subclass_string__when_base_sets_template_filename(self):
        widget = StringOverFileWidget()

        html = widget.render()

        self.assertEqual(html, 'subclass string')

    def test_get_template__renders_file__when_subclass_overrides_get_template_path(self):
        filename = self.write_template('from path {{ data.word }}')

        class PathOverridingWidget(StringTemplateWidget):
            def get_template_path(self):
                return self._find_beside_class_or_bases(filename)

        widget = PathOverridingWidget()

        html = widget.render()

        self.assertEqual(html, 'from path template')

    def test_get_template__renders_instance_string__when_assigned_at_runtime(self):
        widget = StringTemplateWidget()
        widget.template_string = 'instance {{ data.word }}'

        html = widget.render()

        self.assertEqual(html, 'instance template')

    def test_get_template__compiles_once__when_class_rendered_twice(self):
        first_widget = StringTemplateWidget()
        second_widget = StringTemplateWidget()

        first = first_widget.get_template()
        second = second_widget.get_template()

        self.assertIs(first, second)

    def test_get_template__uses_base_string__when_subclass_declares_nothing(self):
        widget = StringInheritingWidget()
        base_widget = StringTemplateWidget()

        html = widget.render()

        template = widget.get_template()
        base_template = base_widget.get_template()
        self.assertEqual(html, 'string template')
        self.assertIs(template, base_template)
