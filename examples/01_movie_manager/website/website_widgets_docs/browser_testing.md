# Browser testing

Testing a page or widget in a real browser without running a server: Chromium, driven by
Playwright, asks for each URL, and Django's test client answers it inside the test's own
transaction. **The package ships none of this.** The movie manager example's
`website/tests/playwright_test_case.py` is a worked base to copy and own; this page explains
why it is built the way it is, so a copy can be changed safely. Read it before writing or
changing a browser test base.

## Why no server

A `StaticLiveServerTestCase` serves the site from another thread, which needs real commits or
shared connections, a `collectstatic`, and a login through the site's form, and it leaves
connections behind on PostgreSQL. Answering each request in-process keeps the test one
transaction: the test creates rows, the browser's requests see them, the test asserts on what
the browser wrote, and the rollback undoes all of it. In the movie manager a page load takes
about 0.05 s and launching the browser 0.2 s per test class.

## How each request is answered

The base routes every request (`context.route('**/*', ...)`):

- **The test host** (`http://testserver`, the test client's default) goes to `self.client`:
  method, path and query, body, and the browser's headers, its `Cookie` header replacing the
  client's own cookies. The response goes back with its status, headers and every `Set-Cookie`,
  so a session cookie an endpoint sets arrives with the browser's next request.
- **`STATIC_URL`** is read from wherever the staticfiles finders find the file, so there is no
  `collectstatic`, but **the frontend must be built first**: a missing `main.js` is a 404, and
  every controller silently never starts, and a stale one runs old code.
  `WebsiteWidgetsTestRunner` builds before any run holding a browser test, tagged `playwright`
  by default (`running_tests.md`); under another runner, nothing does.
- **Every other host is aborted**, so a test never reaches a font CDN, analytics or a sign-in
  script. A test needing one changes the base where it aborts; there is no allowlist.
- **A redirect is made by the base.** When a route answers with a 3xx, Chromium follows it
  straight to the network, skipping the route, so `testserver` fails to resolve. A navigation
  gets a stand-in page that calls `location.replace()` with the `Location`, itself routed, so
  `page.url` ends where a real redirect would; a `fetch()` gets the redirect followed through
  the test client.

**`open_document(html)` answers a reserved test-host URL with the HTML**, rather than
`page.set_content()`, which leaves the page on `about:blank`, where `/static/main.js` can't
resolve. `open_widget(widget, user)` renders the widget with `arender_document()`
(`testing_widgets.md`), signs the browser in as the same user and opens it, so a widget's
controller runs against the same document its server-side tests check.

## Playwright's event loop and Django

Three things the base does, each because of Playwright's sync API, which keeps an asyncio loop
marked as running on the test thread from `start()` to `stop()`:

1. **The test client runs on a short-lived thread.** The test client reaches an async view
   through `async_to_sync()`, which refuses to run on a thread with a running loop. So each
   request is answered on a new thread that borrows the test's database connections
   (`inc_thread_sharing()`, as Django's live server does for SQLite) while the test thread
   waits, so they are never used at once.
2. **The test's connections are put back after `start()`.** While the loop runs, `connections`
   on the test thread hands out *new* connections, outside the class's transaction and its
   `setUpTestData()` rows: SQLite answers "database table is locked", PostgreSQL silently sees
   none of the rows. The base keeps the connections from before `start()` and assigns them back.
3. **`DJANGO_ALLOW_ASYNC_UNSAFE` is set for the class.** With the loop marked as running, every
   query the test itself makes would raise `SynchronousOnlyOperation`, though nothing else runs
   on that loop at the time. The base sets it in `setUpClass()` and restores it in
   `tearDownClass()`.

**The browser lives for one test class**, started in `setUpClass()` and stopped in
`tearDownClass()` before Django rolls back and closes the database. A browser kept for the whole
run would leave the loop running into the test database's teardown, which then refuses to close
its connections.

The async Playwright API with `AsyncClient` avoids the thread and the variable, but ties every
Playwright object to one test's event loop, so each test would launch its own browser, and
every test and its setup would be `async`.

## Running them

Playwright is an optional dependency group in the movie manager, and its browser is a separate
download (`playwright install chromium`), so neither CI nor a plain `poetry install` gets them.
Django imports every test module before applying `--exclude-tag`, so the base imports
Playwright inside a `try` and is decorated `@unittest.skipIf` it's missing, which every browser
test inherits; the base is also tagged `playwright`, for `--exclude-tag=playwright` where it is
installed. **A module never raises `unittest.SkipTest` itself:** unittest stands in a test class
made on the spot for such a module, which `--parallel` can't pickle to send to a worker, so the
whole run crashes. The example's README has the commands.

Because CI never runs them, the recipe can fall behind Playwright or Django; a copy is the
project's to keep working.
