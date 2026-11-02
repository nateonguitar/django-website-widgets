import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.framework_folder import DocsFolder, FrameworkFolder
from website_widgets.management.starter_site import StarterSite


class Command(BaseCommand):
    help = (
        "Creates the website app named by WEBSITE_WIDGETS.website_app_name ('website' by default): "
        "a working starter site, its build files, with package.json depending on the npm package "
        "django-website-widgets, and the folder the package manages: its docs in "
        "website_widgets_docs/. Lists the files and asks before writing. To upgrade an app that "
        "exists, run ww_upgrade.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help='Create the files without asking, and add no docs pointer to CLAUDE.md, .claude/CLAUDE.md or AGENTS.md.')
        parser.add_argument(
            '--project-root',
            help=(
                'The folder the app is created in, and that holds CLAUDE.md, .claude/CLAUDE.md or '
                'AGENTS.md. Defaults to settings.BASE_DIR, or the current directory without one.'))

    def handle(self, *args, **options):
        self.interactive = options['interactive']
        app_label = get_config().website_app_name
        project_root = str(options['project_root'] or getattr(settings, 'BASE_DIR', None) or os.getcwd())
        app_folder = os.path.join(project_root, app_label)
        self._refuse_existing_app(app_label, app_folder)
        self._show_app_name(app_label)

        app_files = StarterSite(app_label).files()
        managed_folders = [
            folder_class(
                app_folder=app_folder,
                stdout=self.stdout,
                interactive=self.interactive)
            for folder_class in FrameworkFolder.managed_folders()
        ]
        managed_paths = [
            f"{managed_folder.RELATIVE_PATH.replace(os.sep, '/')}/{path}"
            for managed_folder in managed_folders
            for path in managed_folder.package_files()
        ]
        self._list_files(app_folder, [*app_files, *managed_paths])
        if self.interactive and not FrameworkFolder.ask('Create these files? [y/N] '):
            self.stdout.write('Nothing was created.')
            return

        for path, content in app_files.items():
            file_path = os.path.join(app_folder, path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        for managed_folder in managed_folders:
            managed_folder.write()
        self.stdout.write(self.style.SUCCESS(f'Created {FrameworkFolder.display_path(app_folder)}/.'))
        docs_folder = DocsFolder(
            app_folder=app_folder,
            stdout=self.stdout,
            interactive=self.interactive)
        docs_folder.offer_docs_pointer(project_root)
        self._show_next_steps(app_label, app_folder)

    @staticmethod
    def _refuse_existing_app(
        app_label: str,
        app_folder: str
    ):
        if not app_label.isidentifier():
            raise CommandError(
                f"WEBSITE_WIDGETS.website_app_name is '{app_label}', which isn't a valid Python "
                f"module name.")
        if any(app_config.label == app_label for app_config in apps.get_app_configs()):
            raise CommandError(
                f"An app labelled '{app_label}' is already installed. To bring its framework files "
                f"up to date, run `python manage.py ww_upgrade`.")
        if os.path.exists(app_folder):
            raise CommandError(
                f'{FrameworkFolder.display_path(app_folder)} already exists. To bring an existing '
                f'website app up to date, add it to INSTALLED_APPS and run `python manage.py ww_upgrade`.')

    def _show_app_name(self, app_label: str):
        if hasattr(settings, 'WEBSITE_WIDGETS'):
            self.stdout.write(
                f"Creating the website app '{app_label}', from WEBSITE_WIDGETS.website_app_name in settings.")
            return
        self.stdout.write(
            f"settings has no WEBSITE_WIDGETS, so the website app takes the default name, "
            f"'{app_label}'. To call it something else, add this to settings.py and run this "
            f"command again:\n"
            f"    from website_widgets.config import WebsiteWidgetsConfig\n"
            f"    WEBSITE_WIDGETS = WebsiteWidgetsConfig(website_app_name='your_app_name')")

    def _list_files(
        self,
        app_folder: str,
        paths: list[str]
    ):
        shown_folder = FrameworkFolder.display_path(app_folder)
        self.stdout.write(f'This creates {len(paths)} files in {shown_folder}/:')
        for path in paths:
            self.stdout.write(f'  {path}')

    def _show_next_steps(
        self,
        app_label: str,
        app_folder: str
    ):
        shown_folder = FrameworkFolder.display_path(app_folder)
        self.stdout.write(
            'Next steps, each a one-line change:\n'
            f"  1. In settings.py, add '{app_label}' to INSTALLED_APPS, so its pages are found "
            f"and its static files served.\n"
            f"  2. In urls.py, add path('', include('{app_label}.urls')) to urlpatterns, importing "
            f"include from django.urls beside path. Its urls.py routes every page with "
            f"@register_url and the starter's JSON endpoint.\n"
            '  3. In manage.py, call start_npm_watch() (from website_widgets) after '
            'DJANGO_SETTINGS_MODULE is set, so runserver rebuilds the TypeScript and SCSS as '
            'you edit them.\n'
            f'  4. In {shown_folder}/, run npm install, for the npm package django-website-widgets, '
            f'webpack and the rest of the build.\n'
            '  5. Run python manage.py runserver and open the home page.\n'
            'Other helpful management commands:\n'
            '  ww_create_page <name>     write a new page\'s files and add it to ts/main.ts\n'
            '  ww_create_widget <name>   write a new widget\'s files and add it to ts/main.ts\n'
            '  ww_create_dialog <name>   write a new dialog\'s files and add it to ts/main.ts\n'
            '  ww_show_routes            list every page\'s URL, in the order Django tries them\n'
            '  ww_doctor                 check the setup and print a fix for each problem\n'
            f'  ww_upgrade                update {shown_folder}/website_widgets_docs/ and the npm '
            f'package\'s range in package.json after upgrading the package')
