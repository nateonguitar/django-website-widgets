import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

from django.apps import apps
from django.contrib.staticfiles import finders
from django.core import checks
from django.core.management.base import BaseCommand

from website_widgets.config import get_config
from website_widgets.management.framework_folder import FrameworkFolder
from website_widgets.management.package_json_check import PackageJsonCheck
from website_widgets.management.starter_site import StarterSite


@dataclass(frozen=True)
class DoctorLine:
    """One line of the checklist, and how to fix it when it failed."""

    passed: bool
    summary: str
    fixes: list[str] = field(default_factory=list)


class Command(BaseCommand):
    help = (
        "Checks a website app's setup and prints a checklist with a fix for each problem: the "
        "package's system checks, Node and npm, package.json against the starter site's, "
        "node_modules, and a built bundle.")
    # Django would stop on a failing check before handle(); this command reports them instead.
    requires_system_checks = []

    # webpack-cli 6, in the starter site's package.json, needs at least this.
    MINIMUM_NODE_VERSION = (18, 12, 0)
    # What webpack.config.js writes and the templates load with {% static %}.
    BUNDLE_FILES = ('main.js', 'bundled-styles.css')
    VERSION_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    # Checked in this order, npm first, since start_npm_watch() and the starter's docs use it.
    PACKAGE_MANAGERS = ('npm', 'yarn', 'pnpm')

    def handle(self, *args, **options):
        """Prints one checklist line per check, each failure followed by its fixes, then a count."""
        version = importlib.metadata.version('django-website-widgets')
        self.stdout.write(f'Checking the setup for django-website-widgets {version}:')
        app_label = get_config().website_app_name
        try:
            messages = self._package_check_messages()
            lines = self._system_check_lines(messages)
        # A broken setup can stop a check itself, as urls.py including an app that isn't
        # installed does, and reporting that is this command's job.
        except Exception as error:
            messages = []
            lines = [DoctorLine(
                passed=False,
                summary=f'The system checks stopped on an error: {type(error).__name__}: {error}',
                fixes=['Run python manage.py check to see where it was raised.'])]
        # E002 already says the app isn't installed, naming the folder it found, so it isn't said twice.
        if not any(message.id == 'website_widgets.E002' for message in messages):
            lines.append(self._app_line(app_label))
        lines.append(self._node_line())
        lines.append(self._package_manager_line())
        app_folder = self._app_folder(app_label)
        if app_folder is not None:
            lines.append(self._package_json_line(app_folder, app_label))
            lines.append(self._node_modules_line(app_folder, app_label))
            lines.append(self._bundle_line(app_folder))

        for line in lines:
            if line.passed:
                self.stdout.write(self.style.SUCCESS(f'[✓] {line.summary}'))
                continue
            self.stdout.write(self.style.ERROR(f'[✗] {line.summary}'))
            for fix in line.fixes:
                self.stdout.write(f'    {fix}')
        problem_count = sum(1 for line in lines if not line.passed)
        if problem_count == 0:
            self.stdout.write('No problems found.')
            return
        self.stdout.write(f'{problem_count} problem{"s" if problem_count != 1 else ""} found.')
        # Non-zero, as `makemigrations --check` exits, so a script or CI job can stop on it.
        sys.exit(1)

    @staticmethod
    def _package_check_messages() -> list[checks.CheckMessage]:
        """The `website_widgets.*` system check messages."""
        return [
            message
            for message in checks.run_checks()
            if message.id and message.id.startswith('website_widgets.')
        ]

    @staticmethod
    def _system_check_lines(messages: list[checks.CheckMessage]) -> list[DoctorLine]:
        """One failed line per package system check message, or one passed line when none fire."""
        if not messages:
            return [DoctorLine(passed=True, summary="The package's system checks pass")]
        return [
            DoctorLine(
                passed=False,
                summary=f'{message.id}: {message.msg}',
                fixes=[message.hint] if message.hint else [])
            for message in messages
        ]

    @staticmethod
    def _app_folder(app_label: str) -> str | None:
        """The installed website app's folder, or `None` when no installed app has the label."""
        try:
            return apps.get_app_config(app_label).path
        except LookupError:
            return None

    def _app_line(self, app_label: str) -> DoctorLine:
        """Whether the app named by `website_app_name` is in INSTALLED_APPS."""
        app_folder = self._app_folder(app_label)
        if app_folder is None:
            return DoctorLine(
                passed=False,
                summary=f"No installed app is labelled '{app_label}', the website app",
                fixes=[
                    f"Add '{app_label}' to INSTALLED_APPS, set WEBSITE_WIDGETS.website_app_name "
                    f"to its label, or create it with python manage.py ww_create_app"])
        return DoctorLine(
            passed=True,
            summary=f"The website app '{app_label}' is installed, at {FrameworkFolder.display_path(app_folder)}/")

    def _node_line(self) -> DoctorLine:
        """Whether node is on the PATH and at least `MINIMUM_NODE_VERSION`."""
        minimum = '.'.join(str(part) for part in self.MINIMUM_NODE_VERSION)
        install_fix = f'Install Node.js {minimum} or newer, which includes npm: https://nodejs.org'
        node_version = self._command_version('node')
        if node_version is None:
            return DoctorLine(
                passed=False,
                summary='node is not on the PATH, so nothing builds the TypeScript or SCSS',
                fixes=[
                    install_fix,
                    'Without Node on this machine, node_and_package_managers.md shows the build in a '
                    'docker or podman container'])
        match = self.VERSION_RE.search(node_version)
        parsed = tuple(int(part) for part in match.groups()) if match else None
        if parsed is not None and parsed < self.MINIMUM_NODE_VERSION:
            return DoctorLine(
                passed=False,
                summary=f'node is {node_version}, older than the build tools need ({minimum})',
                fixes=[install_fix])
        return DoctorLine(passed=True, summary=f'node {node_version}')

    def _package_manager_line(self) -> DoctorLine:
        """
        Whether a JavaScript package manager is on the PATH: npm, which start_npm_watch() runs,
        or one of the others, which a project drives itself.
        """
        for manager in self.PACKAGE_MANAGERS:
            version = self._command_version(manager)
            if version is None:
                continue
            if manager == 'npm':
                return DoctorLine(passed=True, summary=f'npm {version}')
            return DoctorLine(
                passed=True,
                summary=(
                    f'{manager} {version}, with no npm: start_npm_watch() runs npm, so a watcher '
                    f'for {manager} is the project\'s own (node_and_package_managers.md)'))
        return DoctorLine(
            passed=False,
            summary=(
                f"No JavaScript package manager is installed ({', '.join(self.PACKAGE_MANAGERS)}), "
                f"so nothing installs or builds the frontend"),
            fixes=[
                'Install Node.js, which includes npm: https://nodejs.org',
                'Without Node on this machine, node_and_package_managers.md shows the build in a '
                'docker or podman container'])

    @staticmethod
    def _package_json_line(
        app_folder: str,
        app_label: str
    ) -> DoctorLine:
        """Whether the app's package.json has the starter site's build tools, at its versions or newer, and its scripts."""
        shown_folder = FrameworkFolder.display_path(app_folder)
        package_json_check = PackageJsonCheck(
            app_folder=app_folder,
            app_label=app_label)
        fixes = package_json_check.run()
        if fixes.is_empty():
            return DoctorLine(
                passed=True,
                summary=f"{shown_folder}/package.json has the starter site's build tools and scripts")
        return DoctorLine(
            passed=False,
            summary=f"{shown_folder}/package.json lacks what the starter site's build needs",
            fixes=fixes.fix_lines(shown_folder))

    @staticmethod
    def _node_modules_line(
        app_folder: str,
        app_label: str
    ) -> DoctorLine:
        """Whether every build tool in the starter site's devDependencies is in the app's node_modules/."""
        shown_folder = FrameworkFolder.display_path(app_folder)
        starter_package_json = json.loads(StarterSite(app_label).file(StarterSite.PACKAGE_JSON))
        missing = [
            name
            for name in starter_package_json['devDependencies']
            if not os.path.isdir(os.path.join(app_folder, 'node_modules', name))
        ]
        if missing:
            return DoctorLine(
                passed=False,
                summary=f"{shown_folder}/node_modules/ lacks {', '.join(missing)}",
                fixes=[f'In {shown_folder}/, run: npm install'])
        return DoctorLine(passed=True, summary=f'{shown_folder}/node_modules/ has the build tools')

    def _bundle_line(self, app_folder: str) -> DoctorLine:
        """Whether the static file finders find each of `BUNDLE_FILES`, so the build has run."""
        shown_folder = FrameworkFolder.display_path(app_folder)
        missing = [filename for filename in self.BUNDLE_FILES if finders.find(filename) is None]
        if missing:
            return DoctorLine(
                passed=False,
                summary=f"No built {' or '.join(missing)} in the static files, so pages load no TypeScript or styles",
                fixes=[
                    f'In {shown_folder}/, run: npm run build, or start runserver with '
                    f'start_npm_watch() in manage.py'])
        return DoctorLine(passed=True, summary=f"The bundle is built: {', '.join(self.BUNDLE_FILES)}")

    @staticmethod
    def _command_version(command: str) -> str | None:
        """What `<command> --version` prints, or `None` when the command isn't on the PATH."""
        executable = shutil.which(command)
        if executable is None:
            return None
        try:
            result = subprocess.run(
                [executable, '--version'],
                capture_output=True,
                text=True,
                timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() or None
