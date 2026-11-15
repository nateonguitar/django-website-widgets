import json
import os
import shutil
from dataclasses import dataclass

from django.apps import apps
from django.core.management.base import CommandError

from website_widgets.config import get_config


@dataclass(frozen=True)
class WebsiteApp:
    """The website app's label and folder, and its package.json scripts, None when it has no package.json."""

    label: str
    folder: str
    scripts: dict | None

    # Commands that run from the app's installed node_modules/, so a missing one is caught before
    # the command rather than as a "command not found" inside its output.
    NODE_PACKAGE_MANAGERS = ('npm', 'npx', 'pnpm', 'yarn')

    @classmethod
    def from_config(cls) -> 'WebsiteApp':
        label = get_config().website_app_name
        try:
            app_config = apps.get_app_config(label)
        except LookupError:
            raise CommandError(
                f"WEBSITE_WIDGETS.website_app_name is '{label}', but no installed app has that "
                f"label: add the app to INSTALLED_APPS, or set website_app_name to its label.")
        folder = app_config.path
        package_json_path = os.path.join(folder, 'package.json')
        scripts = None
        if os.path.isfile(package_json_path):
            with open(package_json_path) as package_json_file:
                package_json = json.load(package_json_file)
            scripts = package_json.get('scripts', {})
        return cls(label=label, folder=folder, scripts=scripts)

    @property
    def shown_folder(self) -> str:
        """The folder as the developer would type it from where they ran manage.py."""
        return os.path.relpath(self.folder) + os.sep

    @property
    def has_node_modules(self) -> bool:
        return os.path.isdir(os.path.join(self.folder, 'node_modules'))

    def build_problem(self, command: list[str]) -> str | None:
        """Why `command` can't run in this app's folder, in words saying what to change, or None when it can."""
        if command[0] in self.NODE_PACKAGE_MANAGERS and not self.has_node_modules:
            return f'there is no node_modules/: run `npm install` in {self.shown_folder} first'
        is_npm_run = command[0] == 'npm' and len(command) > 2 and command[1] == 'run'
        if is_npm_run and command[2] not in self.scripts:
            return (
                f'{self.shown_folder}package.json has no `{command[2]}` script: add one, or set '
                f'WEBSITE_WIDGETS.testing.build_command to your build command, or None for no build')
        if shutil.which(command[0]) is None:
            return f'{command[0]} was not found, so `{" ".join(command)}` could not run'
        return None
