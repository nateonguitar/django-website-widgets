import os

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from website_widgets.config import get_config
from website_widgets.page import Page


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Command(BaseCommand):
    help = (
        'Generates a page or widget in the website app: its Python class, template, and '
        'optionally a TypeScript controller and a stylesheet, registered in ts/main.ts.')

    TEMPLATES_DIR = os.path.join(PACKAGE_DIR, 'generator_templates')
    FRAMEWORK_FILES = ('app.ts', 'controller.ts')
    # Each pair encloses the lines this command keeps sorted in ts/main.ts.
    MAIN_TS_MARKERS = {
        ('page', 'styles'): '// {{ PAGE STYLES START }}',
        ('widget', 'styles'): '// {{ WIDGET STYLES START }}',
        ('page', 'controllers'): '// {{ PAGE CONTROLLERS START }}',
        ('widget', 'controllers'): '// {{ WIDGET CONTROLLERS START }}',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            'component_type',
            choices=['page', 'widget'],
            help='Whether to generate a page or a widget.')
        parser.add_argument(
            'name',
            help='The component\'s folder and module name, such as "home_page" or "dialogs/login_dialog".')
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
        app_folder = self._website_app_folder(config.website_app_name)
        framework_folder = os.path.join(app_folder, 'ts', 'website_widgets')
        self._require_framework_files(framework_folder)

        component_type = options['component_type']
        full_name = options['name'].strip('/')
        component_name = os.path.basename(full_name)
        module_name = component_name.lower().replace(' ', '_')
        class_name = component_name.replace('_', ' ').title().replace(' ', '')
        target_folder = os.path.join(app_folder, f'{component_type}s', full_name)
        if os.path.exists(target_folder):
            raise CommandError(f'{self._display_path(target_folder)} already exists.')

        replacements = {
            '__ClassName__': class_name,
            '__module_name__': module_name,
            '__framework_path__': self._relative_import_path(framework_folder, target_folder),
        }
        if component_type == 'page':
            app_page_module, app_page_class = self._app_page_class(config)
            replacements['__app_page_module__'] = app_page_module
            replacements['__AppPageClass__'] = app_page_class

        generate_ts = self._choice(options['generate_ts'], 'Generate a TypeScript controller?')
        generate_styles = self._choice(options['generate_styles'], 'Generate a stylesheet?')
        templates_dir = config.generate_component.templates_dir

        os.makedirs(target_folder)
        self._write(target_folder, '__init__.py', '__init__.py.tmpl', templates_dir, replacements)
        self._write(target_folder, f'{module_name}.py', f'{component_type}.py.tmpl', templates_dir, replacements)
        html_template = 'component__controller.html.tmpl' if generate_ts else 'component.html.tmpl'
        self._write(target_folder, f'{module_name}.html', html_template, templates_dir, replacements)

        main_ts_path = os.path.join(app_folder, 'ts', 'main.ts')
        module_from_main_ts = self._relative_import_path(target_folder, os.path.dirname(main_ts_path))
        if generate_styles:
            self._write(target_folder, f'{module_name}.scss', 'component.scss.tmpl', templates_dir, replacements)
            self._insert_into_main_ts(
                main_ts_path,
                self.MAIN_TS_MARKERS[(component_type, 'styles')],
                f"import '{module_from_main_ts}/{module_name}.scss';")
        if generate_ts:
            self._write(target_folder, f'{module_name}.ts', 'controller.ts.tmpl', templates_dir, replacements)
            self._insert_into_main_ts(
                main_ts_path,
                self.MAIN_TS_MARKERS[(component_type, 'controllers')],
                f"export {{ {class_name}Controller }} from '{module_from_main_ts}/{module_name}';")

        self.stdout.write(self.style.SUCCESS(
            f'Generated the {component_type} {class_name} in {self._display_path(target_folder)}.'))
        if generate_ts or generate_styles:
            self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')

    def _website_app_folder(self, app_label: str) -> str:
        try:
            return apps.get_app_config(app_label).path
        except LookupError:
            raise CommandError(
                f"No installed app is labelled '{app_label}'. Add the website app to "
                f"INSTALLED_APPS, or set WEBSITE_WIDGETS.website_app_name to its label.")

    def _require_framework_files(self, framework_folder: str):
        missing = [
            filename for filename in self.FRAMEWORK_FILES
            if not os.path.isfile(os.path.join(framework_folder, filename))
        ]
        if missing:
            raise CommandError(
                f'{self._display_path(framework_folder)} has no {", ".join(missing)}. Run '
                f'`python manage.py init_website_widgets` first: generated controllers import them.')

    def _app_page_class(self, config) -> tuple[str, str]:
        dotted_path = config.generate_component.get_app_page_class(config.website_app_name)
        try:
            page_class = import_string(dotted_path)
        except ImportError:
            raise CommandError(
                f'There is no page base class at {dotted_path}. Create it, or set '
                f'WEBSITE_WIDGETS.generate_component.app_page_class to the dotted path of yours.')
        if not isinstance(page_class, type) or not issubclass(page_class, Page):
            raise CommandError(f'{dotted_path} is not a subclass of website_widgets.Page.')
        module_path, class_name = dotted_path.rsplit('.', 1)
        return module_path, class_name

    def _write(self, folder: str, filename: str, template_name: str, templates_dir: str | None, replacements: dict):
        content = self._read(self._template_path(template_name, templates_dir))
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        with open(os.path.join(folder, filename), 'w', encoding='utf-8') as file:
            file.write(content)

    def _template_path(self, template_name: str, templates_dir: str | None) -> str:
        """The project's template of this name when it has one, otherwise the package's."""
        if templates_dir is not None:
            project_template = os.path.join(templates_dir, template_name)
            if os.path.isfile(project_template):
                return project_template
        return os.path.join(self.TEMPLATES_DIR, template_name)

    def _insert_into_main_ts(self, main_ts_path: str, start_marker: str, line_to_insert: str):
        """Adds the line between a marker pair in main.ts, keeping the section sorted."""
        if not os.path.isfile(main_ts_path):
            self.stderr.write(f'No {self._display_path(main_ts_path)} to add `{line_to_insert}` to.')
            return
        lines = self._read(main_ts_path).splitlines(keepends=True)
        end_marker = start_marker.replace('START', 'END')
        start_index = next((i for i, line in enumerate(lines) if start_marker in line), None)
        end_index = next(
            (i for i, line in enumerate(lines) if start_index is not None and i > start_index and end_marker in line),
            None)
        if start_index is None or end_index is None:
            self.stderr.write(
                f'{self._display_path(main_ts_path)} has no `{start_marker}` ... `{end_marker}` pair; '
                f'add `{line_to_insert}` by hand.')
            return
        section = [line for line in lines[start_index + 1:end_index] if line.strip()]
        if line_to_insert in (line.strip() for line in section):
            return
        section.append(f'{line_to_insert}\n')
        section.sort()
        updated_lines = lines[:start_index + 1] + section + lines[end_index:]
        with open(main_ts_path, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)

    def _choice(self, flag: str | None, question: str) -> bool:
        if flag is not None:
            return flag == 'true'
        while True:
            answer = input(f'{question} [Y/n] ').strip().lower()
            if answer in ('', 'y', 'yes'):
                return True
            if answer in ('n', 'no'):
                return False
            self.stdout.write("Answer 'y' or 'n'.")

    @staticmethod
    def _relative_import_path(target: str, start: str) -> str:
        relative_path = os.path.relpath(target, start).replace(os.sep, '/')
        return relative_path if relative_path.startswith('.') else f'./{relative_path}'

    @staticmethod
    def _display_path(path: str) -> str:
        relative_path = os.path.relpath(path)
        return path if relative_path.startswith('..') else relative_path

    @staticmethod
    def _read(path: str) -> str:
        with open(path, encoding='utf-8') as file:
            return file.read()
