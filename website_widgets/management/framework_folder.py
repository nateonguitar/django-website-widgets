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
    """What a run did to one of the package's files in a managed folder."""

    ADDED = 'added'
    CHANGED = 'changed'
    REMOVED = 'removed'
    UNCHANGED = 'unchanged'


@dataclass(frozen=True)
class FileChange:
    """One file in a managed folder, by its path there, and what this run did to it."""

    path: str
    status: FileStatus


class FrameworkFolder:
    """
    A folder in the website app that the package manages: copied in by `ww_create_app` and
    brought up to the installed version by `ww_upgrade`, both writing it the same way, so a
    created app and an upgraded one hold identical copies. Each subclass names its folder, the
    files it gets and the template of the README that explains it; `managed_folders()` lists
    every one.
    """

    RELATIVE_PATH: str
    README_TEMPLATE_PATH: str
    FILE_LIST_START = '<!-- website_widgets:files -->'
    FILE_LIST_END = '<!-- /website_widgets:files -->'
    FILE_LIST_LINE_RE = re.compile(r'^- `([^`]+)`$')
    VERSION_STAMP_RE = re.compile(r'Copied from django-website-widgets (\S+) by')

    def __init__(
        self,
        app_folder: str,
        stdout: OutputWrapper,
        interactive: bool
    ):
        self.app_folder = app_folder
        self.path = os.path.join(app_folder, self.RELATIVE_PATH)
        self.stdout = stdout
        self.interactive = interactive
        self.version = importlib.metadata.version('django-website-widgets')

    @staticmethod
    def managed_folders() -> list[type['FrameworkFolder']]:
        """Every folder the package manages, in the order the commands write and list them."""
        return [DocsFolder]

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
        A system check: warns for each managed folder copied from another package version than
        the installed one, as when a project upgrades the package and skips `ww_upgrade`. Silent
        without the app or the folder, since a site may use only the Python half.
        """
        try:
            app_folder = apps.get_app_config(get_config().website_app_name).path
        except LookupError:
            return []
        installed = importlib.metadata.version('django-website-widgets')
        warnings = []
        for folder_class in FrameworkFolder.managed_folders():
            stamp = folder_class.read_version_stamp(app_folder)
            if stamp is None or stamp == installed:
                continue
            folder = FrameworkFolder.display_path(os.path.join(app_folder, folder_class.RELATIVE_PATH))
            warnings.append(checks.Warning(
                f'{folder}/ is from django-website-widgets {stamp}, but {installed} is installed, '
                f'so it is out of step with the Python half.',
                hint='Run `python manage.py ww_upgrade`, then commit the folder.',
                id='website_widgets.W001'))
        return warnings

    def source_files(self) -> dict[str, str]:
        """Each file the folder gets from the package, by its path there, before the README."""
        raise NotImplementedError

    def package_files(self) -> dict[str, str]:
        """Each file the folder gets, by its path there, the README last."""
        files = self.source_files()
        file_list = '\n'.join(f'- `{path}`' for path in [*files, 'README.md'])
        readme = self._read(os.path.join(PACKAGE_DIR, self.README_TEMPLATE_PATH))
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
            # A checkout that converts line endings, as git's autocrlf does on Windows, is no change.
            if existed and self._read(file_path).replace('\r\n', '\n') == content.replace('\r\n', '\n'):
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
        moved_to = self._other_folders_by_file()
        for file_change in changes:
            suffix = ''
            filename = os.path.basename(file_change.path)
            if file_change.status == FileStatus.REMOVED and filename in moved_to:
                suffix = f' (moved to {moved_to[filename]}/)'
            elif file_change.status == FileStatus.REMOVED:
                suffix = ' (no longer shipped)'
            self.stdout.write(f'  {file_change.status.value:<10} {file_change.path}{suffix}')
        unchanged_count = len(file_changes) - len(changes)
        if unchanged_count:
            unchanged_label = FileStatus.UNCHANGED.value
            self.stdout.write(f'  {unchanged_label:<10} {unchanged_count} file{"s" if unchanged_count != 1 else ""}')
        self.stdout.write(f'Commit {shown_folder}/ to keep the diff of what changed.')

    def _other_folders_by_file(self) -> dict[str, str]:
        """
        Each file another managed folder ships, by file name, mapped to that folder as shown, so
        a file that moved between folders isn't reported as dropped. By name, since a move can
        also flatten a subfolder, as an older app's `docs/routing.md` lands as `routing.md`.
        """
        folders_by_file = {}
        for folder_class in self.managed_folders():
            if folder_class is type(self):
                continue
            other_folder = folder_class(
                app_folder=self.app_folder,
                stdout=self.stdout,
                interactive=self.interactive)
            for path in other_folder.source_files():
                folders_by_file[os.path.basename(path)] = self.display_path(other_folder.path)
        return folders_by_file

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
        return FrameworkFolder.read_answer(question) in ('y', 'yes')

    @staticmethod
    def read_answer(question: str) -> str:
        """
        The answer, lowercased, or `''`, the question's default, when there is no input to read, as
        when a script runs a command without `--noinput`.
        """
        try:
            return input(question).strip().lower()
        except EOFError:
            print()
            return ''

    @staticmethod
    def display_path(path: str) -> str:
        relative_path = os.path.relpath(path)
        return path if relative_path.startswith('..') else relative_path

    @staticmethod
    def _read(path: str) -> str:
        with open(path, encoding='utf-8', newline='') as file:
            return file.read()


class DocsFolder(FrameworkFolder):
    """
    The app's `website_widgets_docs/`: the package's docs for the version installed, a flat copy
    of its `docs/`, `AGENTS.md` included, which AI coding assistants are pointed at. The docs name
    each other by bare filename, so they read the same in both places.
    """

    RELATIVE_PATH = 'website_widgets_docs'
    README_TEMPLATE_PATH = 'docs_folder_README.md'
    # Where AI coding assistants look for a project's instructions, relative to the project root.
    ASSISTANT_FILES = ('CLAUDE.md', os.path.join('.claude', 'CLAUDE.md'), 'AGENTS.md')
    # Where versions before 0.8.0 copied AGENTS.md, relative to the app, so a pointer one of them
    # added is moved rather than left beside a second.
    PREVIOUS_AGENTS_MD_PATH = os.path.join('ts', 'website_widgets', 'AGENTS.md')

    def source_files(self) -> dict[str, str]:
        files = {}
        docs_dir = os.path.join(PACKAGE_DIR, 'docs')
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith('.md'):
                files[filename] = self._read(os.path.join(docs_dir, filename))
        return files

    def offer_docs_pointer(self, project_root: str):
        """Offers a line pointing AI coding assistants at the copied `AGENTS.md`."""
        target = os.path \
            .relpath(os.path.join(self.path, 'AGENTS.md'), project_root) \
            .replace(os.sep, '/')
        previous_target = os.path \
            .relpath(os.path.join(self.app_folder, self.PREVIOUS_AGENTS_MD_PATH), project_root) \
            .replace(os.sep, '/')
        line = f'- `{target}` — how django-website-widgets works; read before changing pages, widgets or controllers'
        existing = []
        real_paths = set()
        for name in self.ASSISTANT_FILES:
            file_path = os.path.join(project_root, name)
            # A CLAUDE.md linked to AGENTS.md is one file, so it is asked about once.
            real_path = os.path.realpath(file_path)
            if os.path.isfile(file_path) and real_path not in real_paths:
                real_paths.add(real_path)
                existing.append(name)
        if not existing:
            self._offer_new_agents_md(project_root, target, line)
            return
        for name in existing:
            file_path = os.path.join(project_root, name)
            content = self._read(file_path)
            name = name.replace(os.sep, '/')
            if target in content:
                continue
            if previous_target in content:
                self._offer_to_move_pointer(
                    file_path=file_path,
                    name=name,
                    content=content,
                    previous_target=previous_target,
                    target=target)
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

    def _offer_to_move_pointer(
        self,
        file_path: str,
        name: str,
        content: str,
        previous_target: str,
        target: str
    ):
        if not self.interactive:
            self.stdout.write(
                f'{name} points to {previous_target}, which moved to {target}; rerun without '
                f'--noinput to update it.')
            return
        question = (
            f'{name} points AI coding assistants to {previous_target}, which moved to {target}. '
            f'Update it? [y/N] ')
        if self.ask(question):
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                file.write(content.replace(previous_target, target))
            self.stdout.write(f'Updated the pointer in {name}.')

    def _offer_new_agents_md(
        self,
        project_root: str,
        target: str,
        line: str
    ):
        if not self.interactive:
            shown_root = self.display_path(project_root)
            # display_path() gives '.' for the current directory, which reads as a typo in a sentence.
            where = 'the project root' if shown_root == '.' else f'the project root ({shown_root}/)'
            self.stdout.write(
                f'No CLAUDE.md, .claude/CLAUDE.md or AGENTS.md in {where}; '
                f'rerun without --noinput to create an AGENTS.md pointing to {target}.')
            return
        question = (
            f'There is no CLAUDE.md, .claude/CLAUDE.md or AGENTS.md here. Create AGENTS.md pointing '
            f'AI coding assistants to the website_widgets docs ({target})? [y/N] ')
        if self.ask(question):
            with open(os.path.join(project_root, 'AGENTS.md'), 'w', encoding='utf-8') as file:
                file.write(f'{line}\n')
            self.stdout.write('Created AGENTS.md.')
