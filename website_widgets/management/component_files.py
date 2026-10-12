import os
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

    @classmethod
    def parse(cls, name: str) -> 'ComponentName':
        path = name.strip('/')
        component_name = os.path.basename(path)
        return cls(
            path=path,
            module_name=component_name.lower().replace(' ', '_'),
            class_name=component_name.replace('_', ' ').title().replace(' ', ''))


class ComponentFiles:
    """
    The file work `ww_create_page` and `ww_create_widget` both do, called by name from each:
    writing a file from a generator template, adding a line to `ts/main.ts`, and the questions
    and paths around them. It knows nothing about pages or widgets; each command decides what to
    write where.
    """

    TEMPLATES_DIR = os.path.join(PACKAGE_DIR, 'generator_templates')
    FRAMEWORK_FILES = ('app.ts', 'controller.ts')

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

    def require_framework_files(self, app_folder: str):
        """Stops when the framework TypeScript a generated controller imports isn't there."""
        framework_folder = os.path.join(app_folder, FrameworkFolder.RELATIVE_PATH)
        missing = [
            filename for filename in self.FRAMEWORK_FILES
            if not os.path.isfile(os.path.join(framework_folder, filename))
        ]
        if missing:
            raise CommandError(
                f'{FrameworkFolder.display_path(framework_folder)} has no {", ".join(missing)}. Run '
                f'`python manage.py ww_upgrade` first: generated controllers import them.')

    def ask_yes_no(
        self,
        flag: str | None,
        question: str
    ) -> bool:
        """The `--tscontroller`/`--stylesheet` value when given, otherwise the answer, yes by default."""
        if flag is not None:
            return flag == 'true'
        while True:
            answer = input(f'{question} [Y/n] ').strip().lower()
            if answer in ('', 'y', 'yes'):
                return True
            if answer in ('n', 'no'):
                return False
            self.stdout.write("Answer 'y' or 'n'.")

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
    ):
        """Adds the line between a marker pair in `ts/main.ts`, keeping the section sorted."""
        main_ts_path = os.path.join(app_folder, 'ts', 'main.ts')
        shown_path = FrameworkFolder.display_path(main_ts_path)
        if not os.path.isfile(main_ts_path):
            self.stderr.write(f'No {shown_path} to add `{line_to_add}` to.')
            return
        lines = self._read(main_ts_path).splitlines(keepends=True)
        end_marker = start_marker.replace('START', 'END')
        start_index = next((i for i, line in enumerate(lines) if start_marker in line), None)
        end_index = next(
            (i for i, line in enumerate(lines) if start_index is not None and i > start_index and end_marker in line),
            None)
        if start_index is None or end_index is None:
            self.stderr.write(
                f'{shown_path} has no `{start_marker}` ... `{end_marker}` pair; add `{line_to_add}` by hand.')
            return
        section = [line for line in lines[start_index + 1:end_index] if line.strip()]
        if line_to_add in (line.strip() for line in section):
            return
        section.append(f'{line_to_add}\n')
        section.sort()
        updated_lines = lines[:start_index + 1] + section + lines[end_index:]
        with open(main_ts_path, 'w', encoding='utf-8') as file:
            file.writelines(updated_lines)

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
