import os

from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.component_files import ComponentFiles, ComponentName, WrittenFile
from website_widgets.management.framework_folder import FrameworkFolder, TypeScriptFolder


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
        parser.add_argument(
            '--repeating',
            choices=['true', 'false'],
            dest='repeating',
            help=(
                'Shown more than once on a page: the class takes key=, which the root carries in '
                'data-key, so each instance\'s selector finds its own root. Asks when not given '
                'and there is a controller. A widget without one has only a class on its root, '
                'which repeats as it is, so the flag changes nothing.'))
        set_context = parser.add_mutually_exclusive_group()
        set_context.add_argument(
            '--async',
            action='store_const',
            const='async',
            dest='set_context',
            help=(
                'Write `async def set_context()`, for a widget in a page or behind arender(), '
                'where database queries are awaited. The default unless '
                'WEBSITE_WIDGETS.generate_component.widget_set_context says otherwise.'))
        set_context.add_argument(
            '--sync',
            action='store_const',
            const='sync',
            dest='set_context',
            help=(
                'Write `def set_context()`, for a widget rendered with render() from sync code: '
                'a plain Django view, an email, the admin.'))

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
        # Without a controller nothing selects the root, so a class alone serves one instance or many.
        repeating = generate_ts and files.ask_yes_no(
            options['repeating'],
            'Shown more than once on a page?',
            default=False)
        instances = 'repeating' if repeating else 'single'

        framework_folder = os.path.join(app_folder, TypeScriptFolder.RELATIVE_PATH)
        replacements = {
            '__ClassName__': name.class_name,
            '__module_name__': name.module_name,
            '__css_name__': name.css_name,
            '__framework_path__': files.relative_import_path(framework_folder, widget_folder),
        }
        set_context = options['set_context'] or config.generate_component.widget_set_context
        os.makedirs(widget_folder)
        written_files = []
        files.write_from_template(widget_folder, '__init__.py', '__init__.py.tmpl', replacements)
        written_files.append(WrittenFile('__init__.py'))
        files.write_from_template(
            widget_folder,
            f'{name.module_name}.py',
            f'widget__{set_context}__{instances}.py.tmpl',
            replacements)
        set_context_definition = 'async def set_context()' if set_context == 'async' else 'def set_context()'
        class_description = f'{name.class_name}(key=...)' if repeating else name.class_name
        written_files.append(WrittenFile(
            f'{name.module_name}.py',
            f'class {class_description}, with {set_context_definition}'))
        html_template = f'widget__controller__{instances}.html.tmpl' if generate_ts else 'widget__nocontroller.html.tmpl'
        files.write_from_template(widget_folder, f'{name.module_name}.html', html_template, replacements)
        if repeating:
            root_selector = f'.{name.css_name}[data-key=<key>]'
        elif generate_ts:
            root_selector = f'#{name.css_name}'
        else:
            root_selector = f'.{name.css_name}'
        written_files.append(WrittenFile(f'{name.module_name}.html', f'root {root_selector}'))

        # main.ts imports each stylesheet so webpack bundles it, and exports each controller so a
        # template can import it from the bundle.
        from_main_ts = files.relative_import_path(widget_folder, os.path.join(app_folder, 'ts'))
        if generate_ts:
            files.write_from_template(widget_folder, f'{name.module_name}.ts', 'controller.ts.tmpl', replacements)
            exported = files.add_to_main_ts(
                app_folder,
                '// {{ WIDGET CONTROLLERS START }}',
                f"export {{ {name.class_name}Controller }} from '{from_main_ts}/{name.module_name}';")
            written_files.append(WrittenFile(
                f'{name.module_name}.ts',
                f'{name.class_name}Controller, exported from ts/main.ts' if exported else f'{name.class_name}Controller'))
        if generate_styles:
            files.write_from_template(widget_folder, f'{name.module_name}.scss', 'component.scss.tmpl', replacements)
            imported = files.add_to_main_ts(
                app_folder,
                '// {{ WIDGET STYLES START }}',
                f"import '{from_main_ts}/{name.module_name}.scss';")
            written_files.append(WrittenFile(f'{name.module_name}.scss', 'imported in ts/main.ts' if imported else ''))

        self.stdout.write(self.style.SUCCESS(
            f'Created the widget {name.class_name} in {FrameworkFolder.display_path(widget_folder)}/:'))
        self.stdout.write(files.format_file_list(written_files))
        if generate_ts or generate_styles:
            self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')
