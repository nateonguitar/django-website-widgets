import os

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.utils.module_loading import import_string

from website_widgets.config import get_config


class TestRunnerCheck:
    RUNNER_PATH = 'website_widgets.testing.WebsiteWidgetsTestRunner'

    @staticmethod
    def check_test_runner(app_configs=None, **kwargs) -> list[checks.Warning]:
        """
        A system check: warns when the website app has a frontend (a `package.json`) and
        `TEST_RUNNER` isn't `WebsiteWidgetsTestRunner` or a subclass, so `manage.py test` would
        run browser tests against whatever bundle was last built.
        """
        try:
            app_folder = apps.get_app_config(get_config().website_app_name).path
        except LookupError:
            return []
        if not os.path.isfile(os.path.join(app_folder, 'package.json')):
            return []
        runner_path = settings.TEST_RUNNER
        if runner_path == TestRunnerCheck.RUNNER_PATH:
            return []
        try:
            # Imported here, not at module level, so a command that isn't `test` loads the test
            # runner only when the project names its own.
            from website_widgets.testing import WebsiteWidgetsTestRunner
            runner_class = import_string(runner_path)
        except ImportError:
            # `manage.py test` reports a runner that can't be imported, with its traceback.
            return []
        if isinstance(runner_class, type) and issubclass(runner_class, WebsiteWidgetsTestRunner):
            return []
        return [checks.Warning(
            f"TEST_RUNNER is '{runner_path}', so `manage.py test` never builds the frontend: a "
            f"browser test serves whatever bundle was last built.",
            hint=(
                f"Set TEST_RUNNER = '{TestRunnerCheck.RUNNER_PATH}', or subclass it. If the "
                f"project builds before its tests another way, add 'website_widgets.W003' to "
                f"SILENCED_SYSTEM_CHECKS."),
            id='website_widgets.W003')]
