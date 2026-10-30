import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.build_files import BuildFiles
from website_widgets.management.framework_folder import DocsFolder, FrameworkFolder


class Command(BaseCommand):
    help = (
        "Brings the two folders the package manages in the website app, ts/website_widgets/ "
        "(the framework's TypeScript) and website_widgets_docs/ (the package's docs), up to the "
        "installed django-website-widgets, and checks its build files against the starter site's. Run it after every upgrade, and once on an app that never "
        "ran ww_create_app.")
    # It is the fix for the stale-folder warning, so that warning shouldn't open its output, and
    # a page module that fails to import, which stops route discovery's check, mustn't stop it.
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help=(
                'Ask nothing: keep a webpack.config.js or tsconfig.json that differs from the '
                "starter site's, and add no docs pointer to CLAUDE.md, .claude/CLAUDE.md or AGENTS.md."))
        parser.add_argument(
            '--project-root',
            help=(
                'The folder holding CLAUDE.md, .claude/CLAUDE.md or AGENTS.md. Defaults to '
                'settings.BASE_DIR, or the current directory without one.'))

    def handle(self, *args, **options):
        app_label = get_config().website_app_name
        app_folder = self._website_app_folder(app_label)
        for folder_class in FrameworkFolder.managed_folders():
            managed_folder = folder_class(
                app_folder=app_folder,
                stdout=self.stdout,
                interactive=options['interactive'])
            file_changes = managed_folder.write()
            managed_folder.report(file_changes)
        build_files = BuildFiles(
            app_folder=app_folder,
            app_label=app_label,
            stdout=self.stdout,
            interactive=options['interactive'])
        build_files.update()
        project_root = options['project_root'] or getattr(settings, 'BASE_DIR', None) or os.getcwd()
        docs_folder = DocsFolder(
            app_folder=app_folder,
            stdout=self.stdout,
            interactive=options['interactive'])
        docs_folder.offer_docs_pointer(str(project_root))

    @staticmethod
    def _website_app_folder(app_label: str) -> str:
        try:
            return apps.get_app_config(app_label).path
        except LookupError:
            raise CommandError(
                f"No installed app is labelled '{app_label}'. Add the website app to "
                f"INSTALLED_APPS, or set WEBSITE_WIDGETS.website_app_name to its label. To create "
                f"a new website app, run `python manage.py ww_create_app`.")
