# Choosing a test

A site built on the package can test the same behaviour in several places, from a page rendered
by Django's test client in milliseconds to a real browser at a second or more per test. Read
this before writing a test, to pick the place; the doc named for each kind says how to write it.

**Take the first kind that can see what the test checks.** A browser is the last resort, not
the default: it is the slowest by far, and each step down this list adds cost. The movie
manager example has each kind, named below.

- **A page test** (Django's test client, its HTML parsed with BeautifulSoup) when what's checked
  is in the HTML the server sends:
  - text, links, which buttons and fields exist, attributes;
  - what changes with the viewer (signed in or out, staff or not) or with the data;
  - redirects, status codes, the database after a request.
  - **Not when a script changes it after load.** Check the template first: a field a
    controller fills on load from data it reads holds one value in the HTML and another in a
    browser, so a page test would assert the wrong one.
  - Movie manager: `website/tests/test_movie_page.py`.
- **A widget test** (`WidgetDocumentTestMixin`, `testing_widgets.md`) when it's one widget's
  HTML in states no page happens to show together: signed out, empty, the "choose" variant.
  - Movie manager: `website/widgets/movie_card/test_movie_card.py`.
- **An endpoint test** (the test client) for what an endpoint accepts, refuses and saves:
  validation, permissions, side effects such as an email. A browser test that clicks only to
  reach an endpoint is this test written slowly.
  - Movie manager: `api/tests/test_checkout.py`.
- **A controller test** (Vitest in a fake DOM, `testing_controllers.md`) when it's TypeScript:
  - logic with no DOM at all, such as parsing or formatting;
  - one controller's behaviour, driven by clicks, typing, `change` or pointer events, mounted
    on HTML the project's Python rendered, with the server stubbed at `fetch`.
  - **Not when** it needs layout or measured sizes, two controllers working together, or a
    real page load.
  - Movie manager: `website/widgets/movie_card/movie_card.test.ts`.
- **A browser test** (Playwright driving Chromium, `browser_testing.md`) when nothing above can
  see it:
  - measured boxes and layout: heights, widths, overlays, scrolling;
  - controllers working together, such as a form and a field component inside it;
  - flows across pages: cookies, redirects, reloads, the list page after a save;
  - checking that nothing runs, such as script in user content.
  - The package ships no Playwright base class. The movie manager's
    `website/tests/playwright_test_case.py` is one to copy and own: no server, every request
    Chromium makes answered by Django's test client inside the test's transaction. Its tests
    are `website/tests/test_checkout_browser.py`, `test_sign_in_browser.py` and
    `website/widgets/movie_card/test_movie_card_browser.py`, and its README has the install
    and run commands.

**A browser test that checks one of the cheaper things is worth splitting.** The server-rendered
assertions move to a page test, the controller's own behaviour to a controller test, and what's
left is the part that needed a browser, usually much smaller.

`running_tests.md` covers running them all: the build browser tests need, and `--parallel`.
