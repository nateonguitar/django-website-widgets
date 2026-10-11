import os
import tempfile

from django.test import SimpleTestCase

from website_widgets.tests.sample_widgets import SAMPLE_WIDGETS_DIR


class WidgetTestCase(SimpleTestCase):
    def write_template(self, content: str) -> str:
        """
        Writes a template beside `sample_widgets.py` for one test and returns its bare file name,
        for a sample widget's `template_filename`.
        """
        with tempfile.NamedTemporaryFile('w', suffix='.html', dir=SAMPLE_WIDGETS_DIR, delete=False) as template_file:
            template_file.write(content)
        self.addCleanup(os.remove, template_file.name)
        return os.path.basename(template_file.name)
