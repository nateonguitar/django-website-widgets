import importlib.metadata
import os
import re

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Command(BaseCommand):
    help = (
        "Copies the framework's TypeScript and the package's docs into the website app's "
        "ts/website_widgets/ folder. Rerun it after upgrading django-website-widgets.")

    FRAMEWORK_FOLDER = os.path.join('ts', 'website_widgets')
    FILE_LIST_START = '<!-- website_widgets:files -->'
    FILE_LIST_END = '<!-- /website_widgets:files -->'
    FILE_LIST_LINE_RE = re.compile(r'^- `([^`]+)`$')
    # Where AI coding assistants look for a project's instructions, relative to the project root.
    ASSISTANT_FILES = ('CLAUDE.md', os.path.join('.claude', 'CLAUDE.md'), 'AGENTS.md')

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
        self.interactive = options['interactive']
        folder = self._framework_folder()
        version = importlib.metadata.version('django-website-widgets')
        files = self._package_files(version)
        previous_files = self._previous_file_list(folder)
        statuses = self._write_files(folder, files, previous_files)
        self._report(folder, version, statuses)
        project_root = options['project_root'] or getattr(settings, 'BASE_DIR', None) or os.getcwd()
        self._offer_docs_pointer(str(project_root), folder)

    def _framework_folder(self) -> str:
        app_label = get_config().website_app_name
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(
                f"No installed app is labelled '{app_label}'. Add the website app to "
                f"INSTALLED_APPS, or set WEBSITE_WIDGETS.website_app_name to its label.")
        return os.path.join(app_config.path, self.FRAMEWORK_FOLDER)

    def _package_files(self, version: str) -> dict[str, str]:
        """Each file init writes, by its path in the framework folder, the README last."""
        files = {}
        frontend_dir = os.path.join(PACKAGE_DIR, 'frontend')
        for filename in sorted(os.listdir(frontend_dir)):
            if filename.endswith('.ts'):
                files[filename] = self._read(os.path.join(frontend_dir, filename))
        files['AGENTS.md'] = self._read(os.path.join(PACKAGE_DIR, 'AGENTS.md'))
        docs_dir = os.path.join(PACKAGE_DIR, 'docs')
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith('.md'):
                files[f'docs/{filename}'] = self._read(os.path.join(docs_dir, filename))
        file_list = '\n'.join(f'- `{path}`' for path in [*files, 'README.md'])
        readme = self._read(os.path.join(frontend_dir, 'README.md'))
        files['README.md'] = readme.replace('{version}', version).replace('{file_list}', file_list)
        return files

    def _previous_file_list(self, folder: str) -> list[str]:
        """The files the last run wrote, from the list in the README it left."""
        readme_path = os.path.join(folder, 'README.md')
        if not os.path.isfile(readme_path):
            return []
        readme = self._read(readme_path)
        if self.FILE_LIST_START not in readme or self.FILE_LIST_END not in readme:
            return []
        listed = readme.split(self.FILE_LIST_START, 1)[1].split(self.FILE_LIST_END, 1)[0]
        paths = []
        for line in listed.splitlines():
            match = self.FILE_LIST_LINE_RE.match(line.strip())
            if match and self._is_inside_folder(match.group(1)):
                paths.append(match.group(1))
        return paths

    @staticmethod
    def _is_inside_folder(path: str) -> bool:
        # The list is read back from a file in the project, so it may only name files in the folder.
        return not os.path.isabs(path) and '..' not in path.replace('\\', '/').split('/')

    def _write_files(self, folder: str, files: dict[str, str], previous_files: list[str]) -> list[tuple[str, str]]:
        statuses = []
        for path, content in files.items():
            file_path = os.path.join(folder, path)
            existed = os.path.isfile(file_path)
            if existed and self._read(file_path) == content:
                statuses.append(('unchanged', path))
                continue
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                file.write(content)
            statuses.append(('changed' if existed else 'added', path))
        for path in previous_files:
            file_path = os.path.join(folder, path)
            if path in files or not os.path.isfile(file_path):
                continue
            os.remove(file_path)
            statuses.append(('removed', path))
            self._remove_folder_if_empty(os.path.dirname(file_path), folder)
        return statuses

    @staticmethod
    def _remove_folder_if_empty(subfolder: str, folder: str):
        if os.path.abspath(subfolder) != os.path.abspath(folder) and not os.listdir(subfolder):
            os.rmdir(subfolder)

    def _report(self, folder: str, version: str, statuses: list[tuple[str, str]]):
        shown_folder = self._display_path(folder)
        changes = [(status, path) for status, path in statuses if status != 'unchanged']
        if not changes:
            self.stdout.write(f'{shown_folder}/ is already up to date with django-website-widgets {version}.')
            return
        self.stdout.write(f'Updated {shown_folder}/ to django-website-widgets {version}:')
        for status, path in changes:
            suffix = ' (no longer shipped)' if status == 'removed' else ''
            self.stdout.write(f'  {status:<10} {path}{suffix}')
        unchanged_count = len(statuses) - len(changes)
        if unchanged_count:
            self.stdout.write(f'  {"unchanged":<10} {unchanged_count} file{"s" if unchanged_count != 1 else ""}')
        self.stdout.write(f'Commit {shown_folder}/ to keep the diff of what changed.')

    def _offer_docs_pointer(self, project_root: str, folder: str):
        target = os.path.relpath(os.path.join(folder, 'AGENTS.md'), project_root).replace(os.sep, '/')
        line = f'- `{target}` — how django-website-widgets works; read before changing pages, widgets or controllers'
        existing = [name for name in self.ASSISTANT_FILES if os.path.isfile(os.path.join(project_root, name))]
        if not existing:
            self._offer_new_agents_md(project_root, target, line)
            return
        for name in existing:
            file_path = os.path.join(project_root, name)
            content = self._read(file_path)
            name = name.replace(os.sep, '/')
            if target in content:
                continue
            if not self.interactive:
                self.stdout.write(
                    f'{name} has no pointer to {target}; rerun without --noinput to add one.')
                continue
            question = (
                f'Add a line to {name} pointing AI coding assistants to the website_widgets docs '
                f'({target}), so they follow its conventions? [y/N] ')
            if self._ask(question):
                separator = '' if not content or content.endswith('\n') else '\n'
                with open(file_path, 'a', encoding='utf-8') as file:
                    file.write(f'{separator}{line}\n')
                self.stdout.write(f'Added the pointer to {name}.')

    def _offer_new_agents_md(self, project_root: str, target: str, line: str):
        if not self.interactive:
            self.stdout.write(
                f'No CLAUDE.md, .claude/CLAUDE.md or AGENTS.md in {self._display_path(project_root)}; '
                f'rerun without --noinput to create an AGENTS.md pointing to {target}.')
            return
        question = (
            f'There is no CLAUDE.md, .claude/CLAUDE.md or AGENTS.md here. Create AGENTS.md pointing '
            f'AI coding assistants to the website_widgets docs ({target})? [y/N] ')
        if self._ask(question):
            with open(os.path.join(project_root, 'AGENTS.md'), 'w', encoding='utf-8') as file:
                file.write(f'{line}\n')
            self.stdout.write('Created AGENTS.md.')

    @staticmethod
    def _ask(question: str) -> bool:
        return input(question).strip().lower() in ('y', 'yes')

    @staticmethod
    def _display_path(path: str) -> str:
        relative_path = os.path.relpath(path)
        return path if relative_path.startswith('..') else relative_path

    @staticmethod
    def _read(path: str) -> str:
        with open(path, encoding='utf-8', newline='') as file:
            return file.read()
