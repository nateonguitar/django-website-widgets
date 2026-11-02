import keyword
import os
import re
from dataclasses import dataclass

from django.apps import apps
from django.core.management.base import CommandError, OutputWrapper

from website_widgets.management.framework_folder import FrameworkFolder


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class ComponentName:
    """A component's name as given (`dialogs/login_dialog`), and the names derived from it."""

    path: str
    module_name: str
    class_name: str
    # The root element's id and class, `like-button` for `like_button`.
    css_name: str

    PART_RE = re.compile(r'^[a-z_][a-z0-9_]*$')

    @classmethod
    def parse(cls, name: str) -> 'ComponentName':
        """Stops on a name with a part that can't be a Python module, since route discovery imports every one."""
        path = name.strip('/')
        for part in path.split('/'):
            if not cls.PART_RE.match(part) or keyword.iskeyword(part):
                raise CommandError(
                    f"'{name}' can't be a component name: each part of it, '{part}' here, must be "
                    f"a lowercase Python identifier, such as home_page or account/settings_page.")
        component_name = os.path.basename(path)
        return cls(
            path=path,
            module_name=component_name,
            class_name=component_name.replace('_', ' ').title().replace(' ', ''),
            css_name=component_name.strip('_').replace('_', '-'))

    def get_default_route(self) -> str:
        """
        The route `ww_create_page` offers: the path in kebab case, with a trailing `_page` dropped,
        so `manage_auth_tokens_page` routes to `manage-auth-tokens` and `account/settings_page`
        to `account/settings`.
        """
        parts = self.path.split('/')
        parts[-1] = parts[-1].removesuffix('_page')
        return '/'.join(part.replace('_', '-') for part in parts)


@dataclass(frozen=True)
class WrittenFile:
    """A file a command wrote, and what its line in the command's summary says about it."""

    filename: str
    note: str = ''


class ComponentFiles:
    """
    The file work `ww_create_page`, `ww_create_widget` and `ww_create_dialog` share, called by name from each:
    writing a file from a generator template, adding a line to `ts/main.ts`, and the questions
    and paths around them. It knows nothing about pages or widgets; each command decides what to
    write where.
    """

    TEMPLATES_DIR = os.path.join(PACKAGE_DIR, 'generator_templates')

    def __init__(
        self,
        templates_dir: str | None,
        stdout: OutputWrapper,
        stderr: OutputWrapper
    ):
        # The project's own templates, each replacing the package's template of the same name.
        self.templates_dir = templates_dir
        self.stdout = stdout
        self.stderr = stderr

    @staticmethod
    def website_app_folder(app_label: str) -> str:
        try:
            return apps.get_app_config(app_label).path
        except LookupError:
            raise CommandError(
                f"No installed app is labelled '{app_label}'. Add the website app to "
                f"INSTALLED_APPS, or set WEBSITE_WIDGETS.website_app_name to its label. To create "
                f"one, run `python manage.py ww_create_app`.")

    @staticmethod
    def website_app_module(app_label: str) -> str:
        """The website app's module, which its label need not match."""
        return apps.get_app_config(app_label).name

    def ask_yes_no(
        self,
        flag: bool | None,
        question: str,
        default: bool = True
    ) -> bool:
        """
        The flag's value when `--x` or `--no-x` was given, otherwise the answer, a blank one
        taking the default.
        """
        if flag is not None:
            return flag
        choices = '[Y/n]' if default else '[y/N]'
        while True:
            answer = FrameworkFolder.read_answer(f'{question} {choices} ')
            if answer == '':
                return default
            if answer in ('y', 'yes'):
                return True
            if answer in ('n', 'no'):
                return False
            self.stdout.write("Answer 'y' or 'n'.")

    def template_has(
        self,
        template_name: str,
        text: str
    ) -> bool:
        """Whether the template that will be used, the project's or the package's, holds the text."""
        return text in self._read(self._template_path(template_name))

    def write_from_template(
        self,
        folder: str,
        filename: str,
        template_name: str,
        replacements: dict[str, str]
    ):
        content = self._read(self._template_path(template_name))
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        with open(os.path.join(folder, filename), 'w', encoding='utf-8') as file:
            file.write(content)

    def add_to_main_ts(
        self,
        app_folder: str,
        start_marker: str,
        line_to_add: str
    ) -> bool:
        """
        Adds the line between a marker pair in `ts/main.ts`, keeping the section sorted. False,
        having said which line to add by hand, when there is no `main.ts` or no marker pair.
        """
        main_ts_path = os.path.join(app_folder, 'ts', 'main.ts')
        shown_path = FrameworkFolder.display_path(main_ts_path)
        if not os.path.isfile(main_ts_path):
            self.stderr.write(f'No {shown_path} to add `{line_to_add}` to.')
            return False
        lines = self._read(main_ts_path).splitlines(keepends=True)
        end_marker = start_marker.replace('START', 'END')
        start_index = next((i for i, line in enumerate(lines) if start_marker in line), None)
        end_index = next(
            (i for i, line in enumerate(lines) if start_index is not None and i > start_index and end_marker in line),
            None)
        if start_index is None or end_index is None:
            self.stderr.write(
                f'{shown_path} has no `{start_marker}` ... `{end_marker}` pair; add `{line_to_add}` by hand.')
            return False
        section = [line for line in lines[start_index + 1:end_index] if line.strip()]
        if line_to_add in (line.strip() for line in section):
            return True
        section.append(f'{line_to_add}\n')
        section.sort()
        updated_lines = lines[:start_index + 1] + section + lines[end_index:]
        with open(main_ts_path, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)
        return True

    @staticmethod
    def make_component_folder(
        base_folder: str,
        name: 'ComponentName'
    ) -> list[str]:
        """
        Creates the component's folder under `base_folder` (`pages/` or `widgets/`). Each folder
        a nested name adds on the way, such as `emails/` for `emails/email_document`, gets an
        empty `__init__.py`, so it imports as a package like every other rather than as a
        namespace package. A folder that already exists is left as it is. Returns the paths of
        the `__init__.py` files written.
        """
        written_inits = []
        parent_parts = name.path.split('/')[:-1]
        for depth in range(1, len(parent_parts) + 1):
            folder = os.path.join(base_folder, *parent_parts[:depth])
            if os.path.exists(folder):
                continue
            os.makedirs(folder)
            init_path = os.path.join(folder, '__init__.py')
            with open(init_path, 'w', encoding='utf-8'):
                pass
            written_inits.append(init_path)
        os.makedirs(os.path.join(base_folder, name.path))
        return written_inits

    @staticmethod
    def format_file_list(written_files: list[WrittenFile]) -> str:
        """One indented line per file, its note lined up after the longest name."""
        name_width = max(len(written_file.filename) for written_file in written_files)
        lines = [
            f'  {written_file.filename.ljust(name_width)}   {written_file.note}'.rstrip()
            for written_file in written_files
        ]
        return '\n'.join(lines)

    @staticmethod
    def relative_import_path(
        target: str,
        start: str
    ) -> str:
        relative_path = os.path.relpath(target, start).replace(os.sep, '/')
        return relative_path if relative_path.startswith('.') else f'./{relative_path}'

    def _template_path(self, template_name: str) -> str:
        """The project's template of this name when it has one, otherwise the package's."""
        if self.templates_dir is not None:
            project_template = os.path.join(self.templates_dir, template_name)
            if os.path.isfile(project_template):
                return project_template
        return os.path.join(self.TEMPLATES_DIR, template_name)

    @staticmethod
    def _read(path: str) -> str:
        with open(path, encoding='utf-8') as file:
            return file.read()
