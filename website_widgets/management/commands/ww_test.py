import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from website_widgets.config import get_config


@dataclass(frozen=True)
class StepResult:
    """How one step of the run went: `passed`, `failed` or `skipped`, and why when skipped or failed early."""

    outcome: str
    reason: str = ''


@dataclass(frozen=True)
class WebsiteApp:
    """The website app's label and folder, and its package.json scripts, None when it has no package.json."""

    label: str
    folder: str
    scripts: dict | None

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


class Command(BaseCommand):
    help = (
        "Builds the frontend, then runs the Python tests, then the JS tests: "
        "WEBSITE_WIDGETS.test_build_command (npm run build unless set; None for no build) in the "
        "website app's folder, Django's `test` command with every other argument passed on "
        "(`ww_test --exclude-tag=playwright`), then `npm test` in the same folder. A failed build "
        "stops the run; otherwise both test halves run even when the first fails. It ends with a "
        "line for each step and exits non-zero when any failed. --no-build skips the build for "
        "one run. A website app with no package.json, or none with a test script, runs the Python "
        "tests alone and says so.")

    NO_BUILD_OPTION = '--no-build'
    # Build commands that run from the app's installed node_modules/, so a missing one is caught
    # before the build rather than as a "command not found" inside its output.
    NODE_PACKAGE_MANAGERS = ('npm', 'npx', 'pnpm', 'yarn')

    def add_arguments(self, parser):
        # Only for call_command(); from manage.py the arguments are passed on unparsed.
        parser.add_argument('test_arguments', nargs='*')
        parser.add_argument(self.NO_BUILD_OPTION, action='store_true')

    def run_from_argv(self, argv):
        # Not parsed here: every argument after `ww_test` but --no-build belongs to `test`,
        # options included. So BaseCommand.run_from_argv(), which parses them, isn't used, and
        # what it would do around the command is done here: the system checks, and a
        # CommandError as one line instead of a traceback.
        arguments = argv[2:]
        if '-h' in arguments or '--help' in arguments:
            self.stdout.write(self.help)
            return
        build = self.NO_BUILD_OPTION not in arguments
        test_arguments = [argument for argument in arguments if argument != self.NO_BUILD_OPTION]
        try:
            # Raises SystemCheckError, listing each error, before anything runs. Loading the URLs
            # for the checks raises ImproperlyConfigured for a website app that isn't installed.
            self.check()
            passed = self.run_tests(argv[0], test_arguments, build)
        except (CommandError, ImproperlyConfigured) as error:
            if '--traceback' in arguments:
                raise
            self.stderr.write(f'{type(error).__name__}: {error}')
            return_code = error.returncode if isinstance(error, CommandError) else 1
            sys.exit(return_code)
        if not passed:
            sys.exit(1)

    def handle(self, *args, **options):
        if not self.run_tests(sys.argv[0], options['test_arguments'], not options['no_build']):
            raise CommandError('Tests failed.')

    def run_tests(self, manage_py: str, test_arguments: list[str], build: bool) -> bool:
        """Runs every step, writes the summary, and returns whether none failed."""
        website_app = WebsiteApp.from_config()
        build_result = self.run_build(website_app, build)
        if build_result.outcome == 'failed':
            # Tests against a stale or missing bundle would only fail confusingly.
            python = StepResult('skipped', 'the build failed')
            npm = StepResult('skipped', 'the build failed')
        else:
            python = self.run_python_tests(manage_py, test_arguments)
            npm = self.run_npm_tests(website_app)
        self.stdout.write('')
        self.write_summary_line('Build', build_result)
        self.write_summary_line('Python tests', python)
        self.write_summary_line('npm tests', npm)
        return all(result.outcome != 'failed' for result in (build_result, python, npm))

    def run_build(self, website_app: WebsiteApp, build: bool) -> StepResult:
        command = get_config().test_build_command
        if not build:
            return StepResult('skipped', self.NO_BUILD_OPTION)
        if command is None:
            return StepResult('skipped', 'test_build_command is None')
        if website_app.scripts is None:
            return StepResult('skipped', f'no package.json in the {website_app.label} app')
        if command[0] in self.NODE_PACKAGE_MANAGERS and not website_app.has_node_modules:
            return StepResult('failed', f'no node_modules/: run `npm install` in {website_app.shown_folder} first')
        is_npm_run = command[0] == 'npm' and len(command) > 2 and command[1] == 'run'
        if is_npm_run and command[2] not in website_app.scripts:
            return StepResult(
                'failed',
                f'{website_app.shown_folder}package.json has no `{command[2]}` script: add one, or '
                f'set WEBSITE_WIDGETS.test_build_command to your build command, or None for no build')
        executable = shutil.which(command[0])
        if executable is None:
            return StepResult('failed', f'{command[0]} was not found, so `{" ".join(command)}` could not run')
        self.write_step_heading('Build', ' '.join(command), website_app)
        completed = subprocess.run([executable, *command[1:]], cwd=website_app.folder)
        return StepResult('passed' if completed.returncode == 0 else 'failed')

    def run_python_tests(self, manage_py: str, test_arguments: list[str]) -> StepResult:
        command = ['manage.py', 'test', *test_arguments]
        self.write_step_heading('Python tests', ' '.join(command), None)
        # A process of its own, as manage.py was run, so --settings and the project's test
        # runner apply exactly as they would to `manage.py test`.
        completed = subprocess.run([sys.executable, manage_py, 'test', *test_arguments])
        return StepResult('passed' if completed.returncode == 0 else 'failed')

    def run_npm_tests(self, website_app: WebsiteApp) -> StepResult:
        if website_app.scripts is None:
            return StepResult('skipped', f'no package.json in the {website_app.label} app')
        if 'test' not in website_app.scripts:
            return StepResult('skipped', f'the {website_app.label} app\'s package.json has no test script')
        if not website_app.has_node_modules:
            return StepResult('failed', f'no node_modules/: run `npm install` in {website_app.shown_folder} first')
        npm = shutil.which('npm')
        if npm is None:
            # Unlike start_npm_watch(), which only warns: a test run that quietly skips half its
            # tests reads as a pass.
            return StepResult('failed', 'npm was not found, so `npm test` could not run')
        self.write_step_heading('npm tests', 'npm test', website_app)
        completed = subprocess.run([npm, 'test'], cwd=website_app.folder)
        return StepResult('passed' if completed.returncode == 0 else 'failed')

    def write_step_heading(self, label: str, command_line: str, website_app: WebsiteApp | None):
        """A line before each tool's own output, so the summary's failed step is easy to find above it."""
        heading = f'── {label}: {command_line}'
        if website_app is not None:
            heading = f'{heading} (in {website_app.shown_folder})'
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(heading))
        # The tool's output goes straight to the terminal, so this line must be there first.
        self.stdout.flush()

    def write_summary_line(self, label: str, result: StepResult):
        line = f'{label}: {result.outcome}'
        if result.reason:
            line = f'{line} ({result.reason})'
        if result.outcome == 'failed':
            self.stdout.write(self.style.ERROR(line))
        elif result.outcome == 'skipped':
            self.stdout.write(self.style.WARNING(line))
        else:
            self.stdout.write(self.style.SUCCESS(line))
