import enum
import importlib.metadata
import os
import re
from dataclasses import dataclass

from django.apps import apps
from django.core import checks
from django.core.management.base import OutputWrapper

from website_widgets.config import get_config


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FileStatus(enum.Enum):
    """What a run did to one of the package's files in the framework folder."""

    ADDED = 'added'
    CHANGED = 'changed'
    REMOVED = 'removed'
    UNCHANGED = 'unchanged'


@dataclass(frozen=True)
class FileChange:
    """One file in the framework folder, by its path there, and what this run did to it."""

    path: str
    status: FileStatus


class FrameworkFolder:
    """
    A website app's `ts/website_widgets/`: the framework TypeScript and the package's docs, copied
    in by `ww_create_app` and brought up to the installed version by `ww_upgrade`. Both commands
    write it the same way, so a created app and an upgraded one hold identical copies.
    """

    RELATIVE_PATH = os.path.join('ts', 'website_widgets')
    FILE_LIST_START = '<!-- website_widgets:files -->'
    FILE_LIST_END = '<!-- /website_widgets:files -->'
    FILE_LIST_LINE_RE = re.compile(r'^- `([^`]+)`$')
    VERSION_STAMP_RE = re.compile(r'Copied from django-website-widgets (\S+) by')
    # Where AI coding assistants look for a project's instructions, relative to the project root.
    ASSISTANT_FILES = ('CLAUDE.md', os.path.join('.claude', 'CLAUDE.md'), 'AGENTS.md')

    def __init__(
        self,
        app_folder: str,
        stdout: OutputWrapper,
        interactive: bool
    ):
        self.path = os.path.join(app_folder, self.RELATIVE_PATH)
        self.stdout = stdout
        self.interactive = interactive
        self.version = importlib.metadata.version('django-website-widgets')

    @classmethod
    def read_version_stamp(cls, app_folder: str) -> str | None:
        """The package version the folder's README says it was copied from, or `None`."""
        readme_path = os.path.join(app_folder, cls.RELATIVE_PATH, 'README.md')
        if not os.path.isfile(readme_path):
            return None
        match = cls.VERSION_STAMP_RE.search(cls._read(readme_path))
        return match.group(1) if match else None

    @staticmethod
    def check_version_stamp(app_configs=None, **kwargs) -> list[checks.Warning]:
        """
        A system check: warns when the website app's copies are from another package version
        than the installed one, as when a project upgrades the package and skips `ww_upgrade`.
        Silent without the app or the folder, since a site may use only the Python half.
        """
        try:
            app_folder = apps.get_app_config(get_config().website_app_name).path
        except LookupError:
            return []
        stamp = FrameworkFolder.read_version_stamp(app_folder)
        installed = importlib.metadata.version('django-website-widgets')
        if stamp is None or stamp == installed:
            return []
        folder = FrameworkFolder.display_path(os.path.join(app_folder, FrameworkFolder.RELATIVE_PATH))
        return [checks.Warning(
            f'{folder}/ is from django-website-widgets {stamp}, but {installed} is installed, so '
            f'its TypeScript and docs are out of step with the Python half.',
            hint='Run `python manage.py ww_upgrade`, then commit the folder.',
            id='website_widgets.W001')]

    def package_files(self) -> dict[str, str]:
        """Each file the folder gets, by its path there, the README last."""
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
        files['README.md'] = readme \
            .replace('{version}', self.version) \
            .replace('{file_list}', file_list)
        return files

    def write(self) -> list[FileChange]:
        """
        Overwrites each package file, deletes one the last run wrote that this version no longer
        ships, and leaves every other file in the folder alone.
        """
        files = self.package_files()
        previous_files = self._previous_file_list()
        file_changes = []
        for path, content in files.items():
            file_path = os.path.join(self.path, path)
            existed = os.path.isfile(file_path)
            if existed and self._read(file_path) == content:
                file_changes.append(FileChange(path=path, status=FileStatus.UNCHANGED))
                continue
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                file.write(content)
            status = FileStatus.CHANGED if existed else FileStatus.ADDED
            file_changes.append(FileChange(path=path, status=status))
        for path in previous_files:
            file_path = os.path.join(self.path, path)
            if path in files or not os.path.isfile(file_path):
                continue
            os.remove(file_path)
            file_changes.append(FileChange(path=path, status=FileStatus.REMOVED))
            self._remove_folder_if_empty(os.path.dirname(file_path))
        return file_changes

    def report(self, file_changes: list[FileChange]):
        shown_folder = self.display_path(self.path)
        changes = [
            file_change
            for file_change in file_changes
            if file_change.status != FileStatus.UNCHANGED
        ]
        if not changes:
            self.stdout.write(f'{shown_folder}/ is already up to date with django-website-widgets {self.version}.')
            return
        self.stdout.write(f'Updated {shown_folder}/ to django-website-widgets {self.version}:')
        for file_change in changes:
            suffix = ' (no longer shipped)' if file_change.status == FileStatus.REMOVED else ''
            self.stdout.write(f'  {file_change.status.value:<10} {file_change.path}{suffix}')
        unchanged_count = len(file_changes) - len(changes)
        if unchanged_count:
            unchanged_label = FileStatus.UNCHANGED.value
            self.stdout.write(f'  {unchanged_label:<10} {unchanged_count} file{"s" if unchanged_count != 1 else ""}')
        self.stdout.write(f'Commit {shown_folder}/ to keep the diff of what changed.')

    def offer_docs_pointer(self, project_root: str):
        """Offers a line pointing AI coding assistants at the copied `AGENTS.md`."""
        target = os.path \
            .relpath(os.path.join(self.path, 'AGENTS.md'), project_root) \
            .replace(os.sep, '/')
        line = f'- `{target}` — how django-website-widgets works; read before changing pages, widgets or controllers'
        existing = [
            name
            for name in self.ASSISTANT_FILES
            if os.path.isfile(os.path.join(project_root, name))
        ]
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
            if self.ask(question):
                separator = '' if not content or content.endswith('\n') else '\n'
                with open(file_path, 'a', encoding='utf-8') as file:
                    file.write(f'{separator}{line}\n')
                self.stdout.write(f'Added the pointer to {name}.')

    def _offer_new_agents_md(
        self,
        project_root: str,
        target: str,
        line: str
    ):
        if not self.interactive:
            self.stdout.write(
                f'No CLAUDE.md, .claude/CLAUDE.md or AGENTS.md in {self.display_path(project_root)}; '
                f'rerun without --noinput to create an AGENTS.md pointing to {target}.')
            return
        question = (
            f'There is no CLAUDE.md, .claude/CLAUDE.md or AGENTS.md here. Create AGENTS.md pointing '
            f'AI coding assistants to the website_widgets docs ({target})? [y/N] ')
        if self.ask(question):
            with open(os.path.join(project_root, 'AGENTS.md'), 'w', encoding='utf-8') as file:
                file.write(f'{line}\n')
            self.stdout.write('Created AGENTS.md.')

    def _previous_file_list(self) -> list[str]:
        """The files the last run wrote, from the list in the README it left."""
        readme_path = os.path.join(self.path, 'README.md')
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

    def _remove_folder_if_empty(self, subfolder: str):
        if os.path.abspath(subfolder) != os.path.abspath(self.path) and not os.listdir(subfolder):
            os.rmdir(subfolder)

    @staticmethod
    def ask(question: str) -> bool:
        return input(question).strip().lower() in ('y', 'yes')

    @staticmethod
    def display_path(path: str) -> str:
        relative_path = os.path.relpath(path)
        return path if relative_path.startswith('..') else relative_path

    @staticmethod
    def _read(path: str) -> str:
        with open(path, encoding='utf-8', newline='') as file:
            return file.read()
