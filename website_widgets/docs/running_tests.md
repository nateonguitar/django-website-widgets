# Running tests

`WebsiteWidgetsTestRunner` is Django's test runner with two additions a site with a frontend
needs: it builds the frontend before a run that holds browser tests, and a subclass's patches
cover every test, `--parallel` workers included. Read this when setting up a project's tests,
adding something no test may ever do for real (texting, charging a card), or when a test passes
alone and fails under `--parallel`.

Primary code:
- `website_widgets.testing.WebsiteWidgetsTestRunner` — the runner, `patches()`
- `website_widgets.testing.WebsiteWidgetsParallelTestSuite` — starts the patches in each worker
- `website_widgets.config.TestingConfig` — the build command and the browser test tag
- `website_widgets.management.test_runner_check.TestRunnerCheck` — the `W003` check

## Setting it up

```python
# settings.py
TEST_RUNNER = 'website_widgets.testing.WebsiteWidgetsTestRunner'
```

That is the whole setup for a project keeping the starter site's `package.json` and tagging its
browser tests `playwright`. Otherwise, `TestingConfig` says how:

```python
from website_widgets.config import TestingConfig, WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    testing=TestingConfig(
        build_command=['npm', 'run', 'build:production'],  # default ['npm', 'run', 'build']; None: never build
        browser_test_tag='browser',  # default 'playwright'
    ),
)
```

`build_command` is a list of arguments, run without a shell in the website app's folder; a
string raises a `TypeError` showing the list to write.

**System check `website_widgets.W003` warns when `TEST_RUNNER` is another runner** and the
website app has a `package.json`. A project that builds before its tests some other way, such as
a CI step, silences it the way Django silences any check:
`SILENCED_SYSTEM_CHECKS = ['website_widgets.W003']`.

## Why browser tests need a build

A browser test loads the page, and the page loads the built `main.js` and `bundled-styles.css`
from the app's `static/` (`browser_testing.md`). Nothing about running tests rebuilds them, so
after a TypeScript or SCSS edit a browser test runs the bundle from the last build: old code
passes or fails on behalf of the new. A missing bundle is worse, a 404 that leaves every
controller silently unstarted. The Python tests that never open a browser don't care, and
neither do Vitest's, which compile the TypeScript themselves (`testing_controllers.md`).

## How the runner decides to build

After Django has applied `--tag` and `--exclude-tag`, `build_suite()` looks for a selected test
carrying `browser_test_tag`, on its class or its method. When there is one, it runs
`build_command` once, before any test:

- `manage.py test`, a browser test module, or `--tag=playwright` builds;
- `--exclude-tag=playwright`, or a module with no browser test, builds nothing;
- a browser test that will be skipped (`@skip` or `@skipIf` on its class or method, such as a
  base skipped where Playwright isn't installed) needs no build, so a run whose browser tests
  are all skipped builds nothing;
- `--no-build` runs the browser tests against the last build, for a run repeated with no
  frontend change;
- an app with no `package.json` has no frontend, so nothing is built.

**A setup that can't build stops the run before any test**, with one line saying what to change:
no `node_modules/` (run `npm install`), an `npm run` script `package.json` doesn't have, a
command not on the `PATH`. So does a build that fails, since every browser test after it would
fail for a reason that has nothing to do with what it asserts.

## Patches for the whole run

Some things no test may ever do for real, whatever it's testing: send a text through a paid
provider, charge a card, post to a chat. Patching each in every test that might reach it is a
leak waiting for the first test that forgets. A subclass lists them once:

```python
from unittest.mock import patch

from website_widgets.testing import WebsiteWidgetsTestRunner

from api.text_messages import TextMessages


class TestRunner(WebsiteWidgetsTestRunner):
    @classmethod
    def patches(cls) -> list:
        no_texts = patch.object(TextMessages, 'send')
        return [no_texts]
```

```python
TEST_RUNNER = 'movie_manager.test_runner.TestRunner'
```

**`patches()` returns the patchers unstarted, and the runner starts them**: in the main
process before the first test and stops them after the last, and in each `--parallel` worker as
it starts (below). A test checking that a text went out patches the same target again, inside
the test, to see the call: `send_text = self.enterContext(patch.object(TextMessages, 'send'))`.

Email needs no patch: Django's runner already swaps in the in-memory backend, so `mail.outbox`
holds what a test sent.

**A patch belongs in `patches()`, never started somewhere else in the runner** such as
`setup_test_environment()`, which only the main process runs. Under `--parallel` every test runs
in a worker, so a patch started anywhere else silently covers no test at all.

## `--parallel`

`manage.py test --parallel=4` splits the tests among four worker processes, each on its own copy
of the test database, by test case class: one class's tests always run together, in one worker.
Workers on Python 3.14's Linux default, and on macOS and Windows, start as fresh processes
rather than forks, so nothing the main process did reaches them: not a patch, not a module-level
change, not a cache. Django calls `WebsiteWidgetsParallelTestSuite.process_setup()` first in
each, which the runner has given its own dotted path, so the worker imports the runner class and
starts its `patches()`.

**The build runs once, in the main process, before the workers start**, since they all serve
the same `static/` files.

**A worker sends its results back to the main process by pickling them, and a traceback only
pickles with `tblib` installed.** Without it, a failing test in a worker loses its traceback,
and the runner warns at the start of a parallel run. It belongs in the project's dev
dependencies.

A test that fails only under `--parallel` is usually state the serial run shared by accident:
a patch started outside `patches()`, or a test depending on another class's having run first.
**A test module that raises `unittest.SkipTest` on import crashes a parallel run**
(`Can't pickle <class 'unittest.loader.ModuleSkipped'>`): unittest stands in a class made on the
spot for it, which can't be sent to a worker. Skip with `@skipIf` on the class instead.

**SQLite gives each worker a copy of the test database**, `default_1.sqlite3` and so on, in the
folder the run started from, deleted at the end; a killed run leaves them, so they belong in
`.gitignore` (`*_[0-9]*.sqlite3`).

## `ww_test`

`manage.py ww_test` runs `manage.py test` with every argument it's given, then `npm test` in
the website app's folder, and ends with a line for each (`testing_controllers.md`). The build is
the runner's, so `ww_test --no-build` and `ww_test --parallel=4` reach it through `test`.

## Under pytest

pytest-django never uses `TEST_RUNNER`, so under pytest nothing builds and `patches()` start
nowhere. A project on pytest builds before its browser tests and starts its patches in a
session-scoped fixture in `conftest.py` instead, or runs its browser tests through
`manage.py test`.
