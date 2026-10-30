# Starting the Frontend Watcher

`start_npm_watch()` starts `npm run watch` beside Django's development server, so the frontend
rebuilds while `runserver` serves. Read this before changing how `manage.py` starts, or when two
watchers or none are running.

Primary code:
- `website_widgets.npm_watch` — `NpmWatch`, exported as `start_npm_watch = NpmWatch.start`

## Calling it

In `manage.py`, after `DJANGO_SETTINGS_MODULE` is set and before
`execute_from_command_line()`:

```python
from website_widgets import start_npm_watch


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    start_npm_watch()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

It takes no arguments. The folder it runs npm in is the one holding the app named by
`WebsiteWidgetsConfig.website_app_name`, so that app holds the `package.json`.

## When it starts a watcher

Only when the command is `runserver` (`sys.argv[1]`), and only once per folder:

- **Not in the autoreloader's child.** `runserver` runs `manage.py` again in a child process,
  and again on every reload. The child has `RUN_MAIN=true` in its environment, so only the outer
  process starts a watcher, and a code change doesn't start another.
- **Not when one is already running in that folder.** It looks for a process whose command line
  contains `npm run watch` and whose working directory is the app's folder, so a second
  `runserver`, or a watcher started by hand in a terminal, is reused. A watcher from another
  project on the same machine runs in another folder, so it doesn't count. A process the user
  may not inspect reports no working directory and is skipped.

When npm isn't installed it prints a warning and returns, so the server still starts.

The watcher is a child of the outer server process. Stopping the server with Ctrl+C in a
terminal stops both, since they share the terminal. Started any other way, such as a detached
`docker exec`, the watcher keeps running after the server stops, and the next `runserver`
reuses it.

## Why `django.setup()` runs early

Turning an app label into a folder needs the app registry, which isn't populated yet when
`manage.py` starts. So it calls `django.setup()` itself, then reads
`apps.get_app_config(label).path`. `execute_from_command_line()` sets Django up again
afterwards, which is harmless: the app registry populates once. For any command other than
`runserver` it returns before setting anything up.

## Why `psutil`

It needs every process's command line and working directory, on every platform the package
supports. `psutil` gives both, so it is one of the package's dependencies.
