import os

from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.component_files import ComponentFiles, ComponentName
from website_widgets.management.framework_folder import FrameworkFolder


class Command(BaseCommand):
    help = (
        "Creates a widget in the website app's widgets/: a Widget subclass, its template, and "
        "optionally a TypeScript controller and a stylesheet, registered in ts/main.ts.")

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            help='The widget\'s folder and module name, such as "like_button" or "dialogs/login_dialog".')
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

        name = ComponentName.parse(options['name'])
        widget_folder = os.path.join(app_folder, 'widgets', name.path)
        if os.path.exists(widget_folder):
            raise CommandError(f'{FrameworkFolder.display_path(widget_folder)} already exists.')
        generate_ts = files.ask_yes_no(options['generate_ts'], 'Generate a TypeScript controller?')
        generate_styles = files.ask_yes_no(options['generate_styles'], 'Generate a stylesheet?')

        framework_folder = os.path.join(app_folder, FrameworkFolder.RELATIVE_PATH)
        replacements = {
            '__ClassName__': name.class_name,
            '__module_name__': name.module_name,
            '__framework_path__': files.relative_import_path(framework_folder, widget_folder),
        }
        os.makedirs(widget_folder)
        files.write_from_template(widget_folder, '__init__.py', '__init__.py.tmpl', replacements)
        files.write_from_template(widget_folder, f'{name.module_name}.py', 'widget.py.tmpl', replacements)
        html_template = 'component__controller.html.tmpl' if generate_ts else 'component.html.tmpl'
        files.write_from_template(widget_folder, f'{name.module_name}.html', html_template, replacements)

        # main.ts imports each stylesheet so webpack bundles it, and exports each controller so a
        # template can import it from the bundle.
        from_main_ts = files.relative_import_path(widget_folder, os.path.join(app_folder, 'ts'))
        if generate_styles:
            files.write_from_template(widget_folder, f'{name.module_name}.scss', 'component.scss.tmpl', replacements)
            files.add_to_main_ts(
                app_folder,
                '// {{ WIDGET STYLES START }}',
                f"import '{from_main_ts}/{name.module_name}.scss';")
        if generate_ts:
            files.write_from_template(widget_folder, f'{name.module_name}.ts', 'controller.ts.tmpl', replacements)
            files.add_to_main_ts(
                app_folder,
                '// {{ WIDGET CONTROLLERS START }}',
                f"export {{ {name.class_name}Controller }} from '{from_main_ts}/{name.module_name}';")

        self.stdout.write(self.style.SUCCESS(
            f'Created the widget {name.class_name} in {FrameworkFolder.display_path(widget_folder)}.'))
        if generate_ts or generate_styles:
            self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')
