# Movie manager

A family's shared movie shelf, on the honor system: see what's new, search the shelf, put movies
in a cart, say "I'm taking these", and return them when they're back. It's a whole site built the way
django-website-widgets means one to be, from `ww_create_app` on, with TypeScript controllers,
SCSS and webpack, a Django Ninja API and real sign-in.

```bash
poetry install
poetry run python manage.py migrate
cd website && npm install && npm run build && cd ..
poetry run python manage.py runserver
```

Then open http://localhost:8000/ and sign in as `alex`, `jordan` or `sam`, password
`try-the-widgets`. `sam` is also a superuser, for `/admin/`. The site and the admin share
Django's session, so signing in on either signs in on both. `runserver` also starts `npm run watch`, so TypeScript
and SCSS rebuild as you edit them. Tests: `poetry run python manage.py test`.

The tests parse each page with BeautifulSoup, a dev dependency, and find what they check with
the same class names the SCSS and controllers use (`.movie-card__title`, `#account-menu dialog`),
rather than matching strings of HTML. Lines of JavaScript, such as a controller's
`App.initController()` call, are still checked as text.

## How it was made

`django-admin startproject movie_manager .`, `python manage.py startapp api`, then
`python manage.py ww_create_app` and its next steps, then `ww_create_page` for each page and
`ww_create_widget` for each widget. Everything after that was written by hand: the starter's demo
page and endpoint were deleted, and its `AppPage`, `AppState`, `AppUrls` and document template
grew what this site needs.

## Where to look

| What | Where |
| --- | --- |
| The models: `Movie`, one `Copy` per disc, a `Rental` per time someone takes one | `api/models.py` |
| The API, one endpoint per file, its request and response schemas above it, every status in `response={...}` and returned as `Status(code, schema)`; documented at `/api/docs` | `api/endpoints/` |
| The admin, at `/admin/`, a file per model: copies on the shelf, a "still out" filter, a "mark returned" action, the movie page's `CopyTable` widget on each movie, the site's `RatingPicker` as the rating field, and a Return button on each rental still out | `api/admin/` |
| Emails, built from widgets and printed to `runserver`'s console rather than sent | `website/emails/`, `website/widgets/emails/` |
| Every page's base: the user and CSRF token in `context.page`, the 401/403/404 variants | `website/pages/app_page.py` |
| Data every page shares, handed to the frontend once | `website/pages/document_template.html`, `website/ts/app-state.ts` |
| URLs for the frontend, never written into TypeScript | `website/widgets/app_urls/`, `website/ts/app-urls.ts` |

- **Three ways a page gets what it shows.** The home page (`website/pages/home_page/`) queries
  this month's arrivals itself. Find a movie (`find_movie_page/`) takes its search from the URL's
  query string, `/find?genre=horror&rating=R`, so a search can be bookmarked or shared: it
  renders those results on the server, its form is a plain GET form that works without
  JavaScript, and its controller rewrites the URL with `history.replaceState()` as you search.
  A movie's page (`movie_page/`) takes it from the route, `@register_url('movies/<int:movie_id>')`,
  whose `movie_id` reaches the page's constructor; an unknown id raises `NotFoundException` and
  gets the site's own 404.
- **Search answers with HTML.** `api/endpoints/movies/endpoint_search_movies.py` renders
  `MovieResults` with `arender()`, the same widget `FindMoviePage` renders for the search in its
  URL, so a movie card's markup lives in one template. The page inserts the answer with
  `createContextualFragment()` rather than `innerHTML`, so each card's `<script>` runs and starts
  its controller. The endpoint waits half a second (`SEARCH_DELAY_SECONDS`) before answering, so
  the spinner that takes the results' place while a search runs is visible on a local machine.
- **A widget repeated on a page** (`MovieCard`, `RentalRow`) takes a keyword-only `key`, as
  `ww_create_widget --repeating` writes it, and each caller passes the row's id,
  `MovieCard(movie=movie, key=movie.id)`. The root carries it in `data-key`, which its selector
  finds it by, `.movie-card[data-key="{{ data.key }}"]`, beside the `data-movie-id` its
  controller reads. The controller looks its elements up inside that root.
- **The cart is in `localStorage`** (`website/ts/cart.ts`), one per user, so it survives reloads
  and two people on one computer don't share it. Checkout is one transaction: either every movie
  is recorded as taken, or the endpoint answers 409 naming what ran out and nothing is recorded,
  and the cart page asks whether to take the rest. A unique constraint on open rentals stops two
  checkouts taking the same disc.
- **A dialog you `await`.** `ConfirmDialogController.show()` (`website/widgets/confirm_dialog/`)
  returns a promise of the answer (`true`, `false`, or `null` when dismissed without one, as a
  click outside isn't a no), so the cart page reads
  `const takeTheRest = await ConfirmDialogController.show(...)` top to bottom.
  The answer comes from a click that happens later, so `show()` hands back a `Completer`'s promise
  and the dialog's `close` event resolves it: a button stores its choice and closes the dialog,
  and Escape or a click outside closes it with nothing stored. Each call clones the `<template>` the document
  renders into a `<dialog>` of its own, with its own controller and Completer, so questions asked
  back to back, or one over another, never get each other's answers. Two halves own a dialog.
  `DialogFrame` (`website/widgets/dialog_frame/`) is the only widget that renders a `<dialog>`,
  inside a `<template>`, around the dialog's own content widget:
  `DialogFrame(name='confirm-dialog', content=ConfirmDialog())`. `DialogController`
  (`website/ts/dialog-controller.ts`) is the base a dialog's controller extends: its `show()` is one
  call to `openFrame('confirm-dialog', controller)`, which clones the frame and hands the controller the
  clone as a typed `dialog`, and it says what it answers in `answer()`. The dialog, not its
  caller, decides whether a click on the backdrop closes it.
- **The appbar is a singleton** (`static readonly singleton = true`, which `App.initController()`
  reads) other controllers reach with `AppbarController.instance()`, which waits on its
  `Completer`, to update the cart count.
- **Every controller is started by its template's `<script>`**,
  `await App.initController(new MovieCardController(), '.movie-card[data-key="{{ data.key }}"]')`, so
  the selector sits beside the root it names and no controller has a static starter of its own.
- **One service per API router** (`website/ts/api/`): `AuthApiService`, `MovieApiService` and
  `RentalApiService`, each a singleton reached through `.instance`, with a method per endpoint.
  Their base, `ApiService`, sends every request, so the CSRF header (from `AppState`, since the
  cookie is HttpOnly) is written once. Each method's return type mirrors its endpoint's Ninja
  `response={...}`, a union of `ApiResult<status, body>`, so checking `result.status === 201`
  narrows `result.body` to that status's schema. Any status the endpoint doesn't declare, or no
  connection, throws an `ApiError`.
- **Sign-in** (`website/pages/sign_in_page/`) shows what trips people up with `fetch`: the button
  disabled while the request runs, each field's error from a 400, a message for any other
  answer or no connection, and `next` followed only to a path on this site.
- **Refusals are real pages.** The cart, My movies and Add to inventory raise
  `UnauthorizedException` for a signed-out visitor; the 401 page links to sign-in with `next`.
- **A widget inside a widget, each with its own controller.** `Appbar` places `AccountMenu`
  (`website/widgets/account_menu/`) as a child; the appbar's controller keeps the cart count, the
  menu's keeps the theme and signing out. The menu takes no user in its constructor: it reads
  `page.user`, which `AppPage` loads once into `context.page`, the context every widget in the
  tree shares. `context.data` is each widget's own, for what only it works out.
- **Light, dark or the system's theme**, chosen in the dialog the appbar's username opens, beside
  Sign out. Every colour is a CSS variable in `website/ts/styles.scss`, with dark values under
  `[data-theme="dark"]` and under `[data-theme="system"]` when the system prefers dark. The
  choice is a cookie `AppPage` reads, so `<html data-theme>` arrives with the page and a dark
  page never flashes light; `website/ts/theme.ts` writes it, and the chart, drawn on a canvas
  that can't use `var()`, redraws in the new colours.
- **A library from npm.** `npm install chart.js` added it to `website/package.json` beside the
  build tools `ww_create_app` wrote; `ww_upgrade` never edits that file, so a project's own
  dependencies are safe there. My history (`website/pages/my_history_page/`) charts checkouts per
  day from counts the page puts in `data-` attributes on its root, and loads Chart.js with a
  dynamic `import()`, so webpack puts it in its own chunk in `static/chunks/` that only that page
  downloads, rather than in the `main.js` every page loads.
- **The seed** (`api/migrations/0002_seed_family_and_movies.py`) generates a year of history from
  a fixed random seed, so every `migrate` and test run gets the same rows, and no disc is ever
  with two people at once.
- **A card that doesn't know its page** (`purpose='choose'` on the add-to-inventory page)
  dispatches a bubbling `movie-chosen` event, and the page listens for it.
- **Emails are widgets too.** Checking out sends a receipt, and returning a movie sends another,
  each printed to `runserver`'s console. Each email is a class (`website/emails/`) holding its
  subject, a plain-text body and its HTML: its own content widget inside `EmailDocument`, which
  places the `EmailFooter` every email shares. They're rendered with `render()`, sync and with no
  request, so every link is `SITE_URL` plus a path.
- **One widget, on the site and in the admin.** `CopyTable` is the movie page's table of copies,
  and the Movie admin's change page shows the same widget, rendered with `render()` into a
  read-only field. Each loads the copies its own way (the page with the async ORM, the admin with
  the sync one) and passes them in.
- **A widget as a working form field.** `RatingPicker` (`website/widgets/rating_picker/`) is a
  rating `<select>` that says what the chosen rating means. The add-to-inventory page places it
  as a child, and the Movie admin uses it as the rating field through `RatingSelect`, a
  `forms.Select` whose `render()` returns the widget's. One `RatingPickerController` runs in
  both: the widget's `<script>` imports it from the bundle, which loads in the admin like
  anywhere else. The site's stylesheet doesn't, so the picker's own look is inline styles.
- **A small widget for consistency.** `Timestamp` (`website/widgets/timestamp/`) is how every
  date is written: a `<time>` with the moment in `datetime`, the exact time on hover, and the
  text as a date, "4 days ago" or "4 days". A template filter can't write markup, so it's a
  widget, and every table that shows dates nests one per row: Who has what, My history and the
  copy table each build a row widget per rental or copy (`WhoHasWhatRow`, `HistoryRow`,
  `CopyTableRow`) whose children are its `Timestamp`s, and My movies' `RentalRow` nests one too.
  My history's few hundred rows are a few hundred small renders; a much longer list would
  paginate.
- **A widget only the admin uses, in vanilla JavaScript.** `ReturnRentalField`
  (`api/admin/widgets/return_rental_field/`) is the Rental admin's "Returned" field: how long
  ago the copy came back, or how long it's been out and a Return button. Both times are the
  site's own `Timestamp`, nested in this admin-only widget. The button's script, a few lines in the
  widget's own template rather than a controller in the bundle, calls the same return endpoint
  My movies does, which lets staff return anyone's copy and emails the receipt to whoever had it.
  `returned_at` is never a form input there, so saving a form opened before the click can't undo
  it.
