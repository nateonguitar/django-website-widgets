import os
from argparse import BooleanOptionalAction

from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.component_files import ComponentFiles, ComponentName, WrittenFile
from website_widgets.management.framework_folder import FrameworkFolder


class Command(BaseCommand):
    help = (
        "Creates a dialog in the website app's widgets/: a SyncWidget rendering the dialog's "
        "<template>, its DialogController with a static show(), and optionally a stylesheet, "
        "registered in ts/main.ts.")

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            help='The dialog\'s folder and module name, such as "confirm_dialog" or "dialogs/login_dialog".')
        parser.add_argument(
            '--stylesheet',
            action=BooleanOptionalAction,
            dest='generate_styles',
            help='Generate a stylesheet, or not with --no-stylesheet. Asks when neither is given.')

    def handle(self, *args, **options):
        config = get_config()
        files = ComponentFiles(
            templates_dir=config.generate_component.templates_dir,
            stdout=self.stdout,
            stderr=self.stderr)
        app_folder = files.website_app_folder(config.website_app_name)

        name = ComponentName.parse(options['name'])
        dialog_folder = os.path.join(app_folder, 'widgets', name.path)
        if os.path.exists(dialog_folder):
            raise CommandError(f'{FrameworkFolder.display_path(dialog_folder)} already exists.')
        generate_styles = files.ask_yes_no(options['generate_styles'], 'Generate a stylesheet?')

        replacements = {
            '__ClassName__': name.class_name,
            '__module_name__': name.module_name,
            '__css_name__': name.css_name,
        }
        controller_name = f'{name.class_name}Controller'
        package_inits = files.make_component_folder(os.path.join(app_folder, 'widgets'), name)
        written_files = []
        files.write_from_template(dialog_folder, '__init__.py', '__init__.py.tmpl', replacements)
        written_files.append(WrittenFile('__init__.py'))
        files.write_from_template(dialog_folder, f'{name.module_name}.py', 'dialog.py.tmpl', replacements)
        written_files.append(WrittenFile(f'{name.module_name}.py', f'class {name.class_name}(SyncWidget)'))
        files.write_from_template(dialog_folder, f'{name.module_name}.html', 'dialog.html.tmpl', replacements)
        written_files.append(WrittenFile(f'{name.module_name}.html', f'template #{name.css_name}-template'))

        # main.ts exports the controller so a template or another controller can import it from
        # the bundle, and imports the stylesheet so webpack bundles it.
        from_main_ts = files.relative_import_path(dialog_folder, os.path.join(app_folder, 'ts'))
        files.write_from_template(
            dialog_folder,
            f'{name.module_name}.ts',
            'dialog_controller.ts.tmpl',
            replacements)
        exported = files.add_to_main_ts(
            app_folder,
            '// {{ WIDGET CONTROLLERS START }}',
            f"export {{ {controller_name} }} from '{from_main_ts}/{name.module_name}';")
        written_files.append(WrittenFile(
            f'{name.module_name}.ts',
            f'{controller_name}, exported from ts/main.ts' if exported else controller_name))
        if generate_styles:
            files.write_from_template(dialog_folder, f'{name.module_name}.scss', 'component.scss.tmpl', replacements)
            imported = files.add_to_main_ts(
                app_folder,
                '// {{ WIDGET STYLES START }}',
                f"import '{from_main_ts}/{name.module_name}.scss';")
            written_files.append(WrittenFile(f'{name.module_name}.scss', 'imported in ts/main.ts' if imported else ''))

        self.stdout.write(self.style.SUCCESS(
            f'Created the dialog {name.class_name} in {FrameworkFolder.display_path(dialog_folder)}/:'))
        self.stdout.write(files.format_file_list(written_files))
        for init_path in package_inits:
            self.stdout.write(f'Also wrote {FrameworkFolder.display_path(init_path)}, so its folder imports as a package.')
        self.stdout.write(
            f'Place {name.class_name}() as a child of the page or widget it opens from, and open it '
            f'with `await {controller_name}.show()`.')
        self.stdout.write('Run `npm run watch` (or `runserver`, with start_npm_watch()) to rebuild the bundle.')
