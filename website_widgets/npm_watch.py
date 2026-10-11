import os
import subprocess
import sys

import psutil


class NpmWatch:
    """
    Starts `npm run watch` beside `runserver`, so the frontend rebuilds while Django serves. Called
    from `manage.py` as `start_npm_watch()`.
    """

    COMMAND = ['npm', 'run', 'watch']
    COMMAND_LINE = ' '.join(COMMAND)

    @classmethod
    def start(cls):
        """
        Starts `npm run watch` in the folder of the app named by `website_app_name`, when the
        command is `runserver` and no watcher is already running in that folder. Call it in
        `manage.py` after `DJANGO_SETTINGS_MODULE` is set, before `execute_from_command_line()`:

            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
            start_npm_watch()
            execute_from_command_line(sys.argv)

        Sets Django up to find the folder; `execute_from_command_line()` setting it up again is
        harmless, since the app registry only populates once.
        """
        if not cls._should_start(sys.argv, os.environ):
            return
        folder = cls._website_app_folder()
        if cls._is_running_in(folder):
            return
        try:
            subprocess.Popen(cls.COMMAND, cwd=folder)
        except FileNotFoundError:
            # The server is still worth running without the watcher.
            sys.stderr.write(f'start_npm_watch(): npm was not found, so `{cls.COMMAND_LINE}` was not started.\n')

    @staticmethod
    def _should_start(
        argv: list[str],
        environ
    ) -> bool:
        from django.utils.autoreload import DJANGO_AUTORELOAD_ENV

        is_runserver = len(argv) > 1 and argv[1] == 'runserver'
        # The autoreloader runs manage.py again in a child process, and again on every reload;
        # only the outer process starts the watcher.
        is_reloader_child = environ.get(DJANGO_AUTORELOAD_ENV) == 'true'
        return is_runserver and not is_reloader_child

    @staticmethod
    def _website_app_folder() -> str:
        import django
        from django.apps import apps

        from website_widgets.config import get_config

        django.setup()
        app_label = get_config().website_app_name
        return apps.get_app_config(app_label).path

    @classmethod
    def _is_running_in(cls, folder: str) -> bool:
        """
        Whether `npm run watch` is already running in `folder`. Another project's watcher on the
        same machine runs in another folder, so it doesn't count.
        """
        real_folder = os.path.realpath(folder)
        for process in psutil.process_iter(['cmdline', 'cwd']):
            command_line = ' '.join(process.info['cmdline'] or [])
            # `cwd` is None for a process this user may not inspect.
            working_directory = process.info['cwd']
            if cls.COMMAND_LINE not in command_line or working_directory is None:
                continue
            if os.path.realpath(working_directory) == real_folder:
                return True
        return False
