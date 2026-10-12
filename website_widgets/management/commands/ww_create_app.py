import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.framework_folder import FrameworkFolder


class Command(BaseCommand):
    help = (
        "Creates the website app named by WEBSITE_WIDGETS.website_app_name ('website' by default), "
        "with the framework's TypeScript and the package's docs in its ts/website_widgets/. Lists "
        "the files and asks before writing. To upgrade an app that exists, run ww_upgrade.")

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

        app_files = self._app_files(app_label)
        framework_folder = FrameworkFolder(
            app_folder=app_folder,
            stdout=self.stdout,
            interactive=self.interactive)
        framework_paths = [
            os.path.join(FrameworkFolder.RELATIVE_PATH, path)
            for path in framework_folder.package_files()
        ]
        self._list_files(app_folder, [*app_files, *framework_paths])
        if self.interactive and not FrameworkFolder.ask('Create these files? [y/N] '):
            self.stdout.write('Nothing was created.')
            return

        for path, content in app_files.items():
            file_path = os.path.join(app_folder, path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        framework_folder.write()
        self.stdout.write(self.style.SUCCESS(f'Created {FrameworkFolder.display_path(app_folder)}/.'))
        framework_folder.offer_docs_pointer(project_root)
        self._show_next_steps(app_label)

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
            self.stdout.write(f"  {path.replace(os.sep, '/')}")

    @staticmethod
    def _app_files(app_label: str) -> dict[str, str]:
        """The app itself: its package, its `AppConfig`, and the folders the generators fill."""
        config_class_name = ''.join(part.title() for part in app_label.split('_')) + 'Config'
        apps_py = (
            'from django.apps import AppConfig\n'
            '\n'
            '\n'
            f'class {config_class_name}(AppConfig):\n'
            "    default_auto_field = 'django.db.models.BigAutoField'\n"
            f"    name = '{app_label}'\n")
        return {
            '__init__.py': '',
            'apps.py': apps_py,
            os.path.join('pages', '__init__.py'): '',
            os.path.join('widgets', '__init__.py'): '',
        }

    def _show_next_steps(self, app_label: str):
        self.stdout.write(
            'Next steps:\n'
            f"  1. Add '{app_label}' to INSTALLED_APPS in settings.py.\n"
            '  2. Route its pages from urls.py, so every page with @register_url is found:\n'
            '         from website_widgets import PageRoutes\n'
            "         urlpatterns = [path('', PageRoutes.urls()), ...]\n"
            f'  3. Give its pages a base class at {app_label}.pages.app_page.AppPage, a WebPage '
            f'subclass with your document template, before `ww_create_page` (or point '
            f'WEBSITE_WIDGETS.generate_component.app_page_class at yours).\n'
            '  4. Add pages and widgets with `python manage.py ww_create_page <name>` and '
            '`ww_create_widget <name>`.')
