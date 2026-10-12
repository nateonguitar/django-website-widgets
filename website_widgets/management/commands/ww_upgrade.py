import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config
from website_widgets.management.framework_folder import FrameworkFolder


class Command(BaseCommand):
    help = (
        "Brings the website app's ts/website_widgets/ folder, the framework's TypeScript and the "
        "package's docs, up to the installed django-website-widgets. Run it after every upgrade, "
        "and once on an app that never ran ww_create_app.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help='Ask nothing, and add no docs pointer to CLAUDE.md, .claude/CLAUDE.md or AGENTS.md.')
        parser.add_argument(
            '--project-root',
            help=(
                'The folder holding CLAUDE.md, .claude/CLAUDE.md or AGENTS.md. Defaults to '
                'settings.BASE_DIR, or the current directory without one.'))

    def handle(self, *args, **options):
        app_folder = self._website_app_folder()
        framework_folder = FrameworkFolder(
            app_folder=app_folder,
            stdout=self.stdout,
            interactive=options['interactive'])
        file_changes = framework_folder.write()
        framework_folder.report(file_changes)
        project_root = options['project_root'] or getattr(settings, 'BASE_DIR', None) or os.getcwd()
        framework_folder.offer_docs_pointer(str(project_root))

    @staticmethod
    def _website_app_folder() -> str:
        app_label = get_config().website_app_name
        try:
            return apps.get_app_config(app_label).path
        except LookupError:
            raise CommandError(
                f"No installed app is labelled '{app_label}'. Add the website app to "
                f"INSTALLED_APPS, or set WEBSITE_WIDGETS.website_app_name to its label. To create "
                f"a new website app, run `python manage.py ww_create_app`.")
