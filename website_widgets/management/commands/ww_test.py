import shutil
import subprocess
import sys
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from website_widgets.management.website_app import WebsiteApp


@dataclass(frozen=True)
class StepResult:
    """How one step of the run went: `passed`, `failed` or `skipped`, and why when skipped or failed early."""

    outcome: str
    reason: str = ''


class Command(BaseCommand):
    help = (
        "Runs the Python tests, then the JS tests: Django's `test` command with every argument "
        "passed on (`ww_test --exclude-tag=playwright --parallel=4`), then `npm test` in the "
        "website app's folder, even when the first fails. It ends with a line for each and exits "
        "non-zero when either failed. The build before browser tests is the test runner's, "
        "WebsiteWidgetsTestRunner, so `--no-build` goes to `test` too. A website app with no "
        "package.json, or none with a test script, runs the Python tests alone and says so.")

    def add_arguments(self, parser):
        # Only for call_command(); from manage.py the arguments are passed on unparsed.
        parser.add_argument('test_arguments', nargs='*')

    def run_from_argv(self, argv):
        # Not parsed here: every argument after `ww_test` belongs to `test`, options included.
        # So BaseCommand.run_from_argv(), which parses them, isn't used, and what it would do
        # around the command is done here: the system checks, and a CommandError as one line
        # instead of a traceback.
        arguments = argv[2:]
        if '-h' in arguments or '--help' in arguments:
            self.stdout.write(self.help)
            return
        try:
            # Raises SystemCheckError, listing each error, before anything runs. Loading the URLs
            # for the checks raises ImproperlyConfigured for a website app that isn't installed.
            self.check()
            passed = self.run_tests(argv[0], arguments)
        except (CommandError, ImproperlyConfigured) as error:
            if '--traceback' in arguments:
                raise
            self.stderr.write(f'{type(error).__name__}: {error}')
            return_code = error.returncode if isinstance(error, CommandError) else 1
            sys.exit(return_code)
        if not passed:
            sys.exit(1)

    def handle(self, *args, **options):
        if not self.run_tests(sys.argv[0], options['test_arguments']):
            raise CommandError('Tests failed.')

    def run_tests(self, manage_py: str, test_arguments: list[str]) -> bool:
        """Runs both halves, writes the summary, and returns whether neither failed."""
        website_app = WebsiteApp.from_config()
        python = self.run_python_tests(manage_py, test_arguments)
        npm = self.run_npm_tests(website_app)
        self.stdout.write('')
        self.write_summary_line('Python tests', python)
        self.write_summary_line('npm tests', npm)
        return all(result.outcome != 'failed' for result in (python, npm))

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
