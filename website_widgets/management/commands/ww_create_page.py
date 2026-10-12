import os
from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from website_widgets.config import WebsiteWidgetsConfig, get_config
from website_widgets.management.component_files import ComponentFiles, ComponentName
from website_widgets.management.framework_folder import FrameworkFolder
from website_widgets.web_page import WebPage


@dataclass(frozen=True)
class PageBaseClass:
    """The class a generated page extends, as its import line will name it."""

    module_path: str
    class_name: str


class Command(BaseCommand):
    help = (
        "Creates a page in the website app's pages/: a subclass of the app's page base class, its "
        "template, and optionally a TypeScript controller and a stylesheet, registered in "
        "ts/main.ts.")

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            help='The page\'s folder and module name, such as "home_page" or "account/settings_page".')
        parser.add_argument(
            '--tscontroller',
            choices=['true', 'false'],
            dest='generate_ts',
            help='Generate a TypeScript controller. Asks when not given.')
        parser.add_argument(
            '--stylesheet',
            choices=['true', 'false'],
            dest='generate_styles',
            help='Generate a stylesheet. Asks when not given.')

    def handle(self, *args, **options):
        config = get_config()
        files = ComponentFiles(
            templates_dir=config.generate_component.templates_dir,
            stdout=self.stdout,
            stderr=self.stderr)
        app_folder = files.website_app_folder(config.website_app_name)
        files.require_framework_files(app_folder)
        # Checked before anything is written, so a missing base class leaves no half-made page.
        page_base_class = self._page_base_class(config)

        name = ComponentName.parse(options['name'])
        page_folder = os.path.join(app_folder, 'pages', name.path)
        if os.path.exists(page_folder):
            raise CommandError(f'{FrameworkFolder.display_path(page_folder)} already exists.')
        generate_ts = files.ask_yes_no(options['generate_ts'], 'Generate a TypeScript controller?')
        generate_styles = files.ask_yes_no(options['generate_styles'], 'Generate a stylesheet?')

        framework_folder = os.path.join(app_folder, FrameworkFolder.RELATIVE_PATH)
        replacements = {
            '__ClassName__': name.class_name,
            '__module_name__': name.module_name,
            '__framework_path__': files.relative_import_path(framework_folder, page_folder),
            '__app_page_module__': page_base_class.module_path,
            '__AppPageClass__': page_base_class.class_name,
        }
        os.makedirs(page_folder)
        files.write_from_template(page_folder, '__init__.py', '__init__.py.tmpl', replacements)
        files.write_from_template(page_folder, f'{name.module_name}.py', 'page.py.tmpl', replacements)
        html_template = 'component__controller.html.tmpl' if generate_ts else 'component.html.tmpl'
        files.write_from_template(page_folder, f'{name.module_name}.html', html_template, replacements)

        # main.ts imports each stylesheet so webpack bundles it, and exports each controller so a
        # template can import it from the bundle.
        from_main_ts = files.relative_import_path(page_folder, os.path.join(app_folder, 'ts'))
        if generate_styles:
            files.write_from_template(page_folder, f'{name.module_name}.scss', 'component.scss.tmpl', replacements)
            files.add_to_main_ts(
                app_folder,
                '// {{ PAGE STYLES START }}',
                f"import '{from_main_ts}/{name.module_name}.scss';")
        if generate_ts:
            files.write_from_template(page_folder, f'{name.module_name}.ts', 'controller.ts.tmpl', replacements)
            files.add_to_main_ts(
                app_folder,
                '// {{ PAGE CONTROLLERS START }}',
                f"export {{ {name.class_name}Controller }} from '{from_main_ts}/{name.module_name}';")

        self.stdout.write(self.style.SUCCESS(
            f'Created the page {name.class_name} in {FrameworkFolder.display_path(page_folder)}.'))
        if generate_ts or generate_styles:
            self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')

    @staticmethod
    def _page_base_class(config: WebsiteWidgetsConfig) -> PageBaseClass:
        """`app_page_class`, the class a generated page extends. Stops when nothing is there, or it isn't a `WebPage`."""
        dotted_path = config.generate_component.get_app_page_class(config.website_app_name)
        try:
            page_class = import_string(dotted_path)
        except ImportError:
            raise CommandError(
                f'There is no page base class at {dotted_path}. Create it, or set '
                f'WEBSITE_WIDGETS.generate_component.app_page_class to the dotted path of yours.')
        if not isinstance(page_class, type) or not issubclass(page_class, WebPage):
            raise CommandError(
                f'{dotted_path} is not a subclass of website_widgets.WebPage.')
        module_path, class_name = dotted_path.rsplit('.', 1)
        return PageBaseClass(
            module_path=module_path,
            class_name=class_name)
