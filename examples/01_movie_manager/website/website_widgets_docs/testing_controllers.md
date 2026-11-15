# Testing controllers

Testing a controller's TypeScript without a browser or a build: Vitest runs it in Node against
a fake DOM (happy-dom), on HTML the project's Python rendered. The package ships `App.clearSingletons()`
for this and nothing else; the movie manager example has the setup worked through
(`website/vitest.config.ts`, `website/tests/fixtures.ts`, the `*.test.ts` files). Read this
before writing a controller test.

Primary code:
- `frontend/src/app.ts` — `App.clearSingletons()`, `App.initController()`

## The setup

- **Vitest and happy-dom are dev dependencies of the website app**, with `"test": "vitest run"`
  in its `package.json`. Vitest compiles TypeScript itself, so no webpack build is needed, and
  webpack never bundles a `.test.ts`, since nothing `main.ts` imports reaches one.
- **`environment: 'happy-dom'`, with script evaluation and file loading switched off**
  (`disableJavaScriptEvaluation`, `disableJavaScriptFileLoading`, `disableCSSFileLoading`,
  `handleDisabledFileLoadingAsSuccess`). A widget's `<script>` imports the built `main.js`; in
  a test, nothing loads it, and the test starts each controller itself.
- **A test lives anywhere** Vitest's default `**/*.test.ts` finds it: beside its widget
  (`widgets/movie_card/movie_card.test.ts`) for one widget's controller, in the app's `tests/`
  for a page's.

## HTML from Python

**A test mounts its controller on HTML the project's Python rendered**, so a template change
reaches the JS tests instead of a hand-copied fragment drifting from it. In the movie manager:

- **Python tests tagged `vitest_fixtures` write the HTML** (`website/tests/test_vitest_fixtures.py`):
  a widget's document from `arender_document()` (`testing_widgets.md`), a page from the test
  client, an endpoint's HTML answer from the test client. They are ordinary tests that also
  write a file, so a plain `manage.py test` runs them too, into one git-ignored folder,
  `website/vitest_fixtures/`.
- **Vitest's `globalSetup` runs them first**, `manage.py test --tag=vitest_fixtures`, so every
  `npm test` uses the current templates. It runs once per Vitest session: under `vitest --watch`
  a template edit needs Vitest restarted to refresh its fixture.
- **`Fixtures.mount(name)` sets the file as `document.body.innerHTML`.** The parser drops the
  `<html>`, `<head>` and `<body>` wrappers, and a `<script>` set that way never runs, so nothing
  the page's scripts would have set is set: a test assigns the `AppState` and `AppUrls` values
  its controller reads.

## Running both halves

`npm test` runs the JS tests, `manage.py test` the Python ones (the fixture writers included),
and **`manage.py ww_test` runs everything** in the website app's folder, found through
`website_app_name`:

1. **The build,** `WEBSITE_WIDGETS.test_build_command`: a list of arguments run without a
   shell, `['npm', 'run', 'build']` by default, any other command in its place
   (`['npm', 'run', 'build:production']`, `['pnpm', 'build']`), `None` for none. The browser
   tests serve the built bundle, so without it they test whatever was last built. A failed
   build stops the run; `--no-build` skips it for one run.
2. **The Python tests,** with every other argument passed to `test`
   (`ww_test --exclude-tag=playwright`).
3. **`npm test`,** even when the Python tests failed.

A heading line before each step names the command and folder, so its output is easy to find,
and a line for each step at the end says how it went, the exit code non-zero when any failed.
**A wrong setup fails before anything runs, in one line saying what to change:** the system
checks run first, as for any Django command (a website app that isn't installed is caught
there); a `package.json` with no `node_modules/` says to run `npm install`; an `npm run <script>`
build whose script isn't in `package.json` names `test_build_command`. `--traceback` shows the
full traceback instead. An app with no `package.json` skips the build and the JS half, saying
so, as does one with no `test` script for the JS half; a `test` script with no `npm` on the path
fails the run. The fixture writers
run twice under `ww_test`, once in each half, a few seconds traded for each half staying
complete on its own.

## Mounting and resetting

A test starts a controller exactly as its template's `<script>` would:
`await App.initController(new MovieCardController(), '.movie-card[data-key="12"]')`.

**Vitest keeps one copy of each module for every test in a file,** so static state carries from
one test into the next. `App.clearSingletons()` in `beforeEach` empties the package's singleton registry;
a project's own static state needs the same, such as a singleton's readiness `Completer`
(`AppbarController.singletonInitializationCompleter = new Completer<null>()`), or a second
test's `instance()` resolves at once to a controller that isn't registered yet.

**happy-dom has what controllers use most:** `<dialog>` with `showModal()` and `close()`,
`<template>`, `localStorage`, `history.replaceState()`, `matchMedia()`. It does no layout, so a
controller measuring elements (`getBoundingClientRect()`, `IntersectionObserver`,
`ResizeObserver`) is a browser test's job (`browser_testing.md`).

## Stubbing the server

**`vi.stubGlobal('fetch', vi.fn())` replaces the browser's `fetch`**, which covers any wrapper a
project sends requests through, with `vi.unstubAllGlobals()` in `afterEach`:

- **JSON is written in the test**, small and shaped like the endpoint's schema; the endpoint's
  own tests hold it to that shape.
- **HTML comes from Python**, as a fixture: the movie manager's search stub answers with what the
  search endpoint really rendered.

A project on another HTTP client mocks that module instead, since a `fetch` stub never sees it:
`vi.mock('axios', ...)` (axios is no global, and under happy-dom it uses `XMLHttpRequest`).
MSW intercepts at the network layer and works for any client.
