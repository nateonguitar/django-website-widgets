import os

from django.test import SimpleTestCase

from website_widgets.tests.sample_widgets import SAMPLE_WIDGETS_DIR, ClassLevelDocumentPage, UnsetDocumentPage


class GetDocumentTemplatePathTestCase(SimpleTestCase):
    def test_get_document_template_path__fails__when_document_template_path_unset(self):
        with self.assertRaises(NotImplementedError):
            UnsetDocumentPage().get_document_template_path()

    def test_get_document_template_path__returns_path_beside_class__when_document_template_path_relative(self):
        self.assertEqual(
            ClassLevelDocumentPage().get_document_template_path(),
            os.path.join(SAMPLE_WIDGETS_DIR, '../templates/document_template.html'))

    def test_get_document_template_path__returns_path_unchanged__when_document_template_path_absolute(self):
        page = UnsetDocumentPage()
        page.document_template_path = '/srv/templates/document_template.html'

        self.assertEqual(page.get_document_template_path(), '/srv/templates/document_template.html')
