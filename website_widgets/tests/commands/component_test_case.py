import io
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from website_widgets.config import GenerateComponentConfig, WebsiteWidgetsConfig


MAIN_TS = '''\
// {{ WIDGET STYLES START }}
import '../widgets/zebra/zebra.scss';
// {{ WIDGET STYLES END }}

// {{ PAGE STYLES START }}
// {{ PAGE STYLES END }}

// {{ WIDGET CONTROLLERS START }}
// {{ WIDGET CONTROLLERS END }}

// {{ PAGE CONTROLLERS START }}
// {{ PAGE CONTROLLERS END }}
'''


class ComponentTestCase(SimpleTestCase):
    """
    A temp website app that `ww_upgrade` has populated, with a main.ts holding the four marker
    pairs and an empty `templates_dir`, for `ww_create_page` and `ww_create_widget`.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_folder = os.path.join(self.project_root, 'website')
        self.templates_dir = os.path.join(self.project_root, 'generator_templates')
        os.makedirs(os.path.join(self.app_folder, 'ts'))
        os.makedirs(self.templates_dir)
        self.write(MAIN_TS, self.app_folder, 'ts', 'main.ts')

        app_config = SimpleNamespace(path=self.app_folder)
        for module in ('commands.ww_upgrade', 'component_files'):
            mock_apps = self.enterContext(patch(f'website_widgets.management.{module}.apps'))
            mock_apps.get_app_config.return_value = app_config
        self.config = WebsiteWidgetsConfig(
            generate_component=GenerateComponentConfig(
                app_page_class='website_widgets.web_page.WebPage',
                templates_dir=self.templates_dir))
        for command in ('ww_create_page', 'ww_create_widget'):
            self.enterContext(patch(
                f'website_widgets.management.commands.{command}.get_config',
                side_effect=lambda: self.config))

        call_command(
            'ww_upgrade',
            '--noinput',
            '--project-root',
            self.project_root,
            stdout=io.StringIO())

    def run_command(self, command: str, *args: str) -> str:
        output = io.StringIO()
        call_command(command, *args, stdout=output, stderr=output)
        return output.getvalue()

    def read(self, *path_parts: str) -> str:
        with open(os.path.join(*path_parts), encoding='utf-8') as file:
            return file.read()

    def write(self, content: str, *path_parts: str):
        with open(os.path.join(*path_parts), 'w', encoding='utf-8') as file:
            file.write(content)
