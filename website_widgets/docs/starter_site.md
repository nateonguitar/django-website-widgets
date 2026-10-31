# The Starter Site

`python manage.py ww_create_app` writes a working website into the new app: a page that calls a
JSON endpoint, a page that is always refused, the document every page renders into, and the
webpack build. Run it once and the whole round trip works, from Python through the template and
the bundle to an endpoint and back. Read this to learn what each starter file is for, and which
conventions it shows, before replacing it with a real site.

Primary code:
- `website_widgets.management.starter_site.StarterSite` — writes the files, from the package's `starter_site/` templates
- `website_widgets.management.commands.ww_create_app` — the command that calls it

**Every starter file is yours from the moment it's written.** The package never touches one
again: `ww_upgrade` keeps only its two managed folders up to date, and checks the build files
(below). Edit, rename or delete them freely.

## The files

```
<app>/
├── apps.py                 the AppConfig, named for the app (WebsiteConfig)
├── urls.py                 PageRoutes.urls() and the endpoint, included by the project's urls.py
├── exceptions.py           the exceptions AppPage turns into a status code and a variant template
├── endpoints/
│   └── greeting_endpoint.py   GreetingEndpoint, a plain Django view returning JSON
├── pages/
│   ├── app_page.py         AppPage(WebPage), the base of every page
│   ├── app_page__unauthorized.html, app_page__forbidden.html, app_page__not_found.html
│   ├── document_template.html  the document every page renders into
│   ├── home_page/          HomePage at '/', with a controller and a stylesheet
│   └── forbidden_example_page/  ForbiddenExamplePage, always refused
├── widgets/
│   └── app_urls/           the AppUrls widget, handing URLs to TypeScript
├── ts/
│   ├── main.ts             the bundle's entry point, with the commands' four marker pairs,
│   │                       and where the custom elements are defined
│   ├── app-state.ts        AppState: data every page shares
│   ├── app-urls.ts         AppUrls: the URLs the frontend reads
│   ├── styles.scss         styles every page shares
│   ├── web-components/loading-spinner.ts and .scss
│   └── website_widgets/    the framework TypeScript, managed by the package, not yours
├── website_widgets_docs/   the package's docs and AGENTS.md, managed by the package, not yours
├── package.json, webpack.config.js, tsconfig.json
└── .gitignore              node_modules/
```

`main.ts` builds to `static/main.js` and `static/bundled-styles.css` in the app, which Django's
app directories finder serves. Templates import from the bundle as an ES module,
`import { AppState } from '{% static "main.js" %}'`, so `main.ts` exports what they use.

## `AppPage` and refusals

`AppPage` is where a site puts what every page shares: the document template, the title format,
and the widgets the document renders (`app_urls`). `ww_create_page` generates pages from it, at
`<app>.pages.app_page.AppPage`, the default `app_page_class`.

Its `handle_request()` catches the exceptions in `exceptions.py`, raised from any page's
`set_context()`: `UnauthorizedException` (401), `ForbiddenException` (403) and
`NotFoundException` (404) each set the page's status code and its variant template,
`app_page__<variant>.html`, with the exception's message as `data.message`; whatever
`set_context()` had set before it raised is dropped. `RedirectException` carries a redirect
response, which is returned as it is. `ForbiddenExamplePage` always raises, so the refusal path
can be seen working; its own template says it is never shown.

## How data reaches a controller

The home page's controller shows both ways, by who needs the data:

- **Data every page shares is on `AppState`**, set once by `document_template.html` before any
  controller runs. The starter sets the site name there, from `AppPage.SITE_NAME` through
  `context.page`, and the controller shows it with the endpoint's answer. Any controller imports
  `AppState` and reads it.
- **Data only one element needs is a `data-` attribute on that element**, the root the
  selector the template passes to `App.initController()` finds, read from
  `this.__element.dataset`. `HomePage` puts
  the default name there.

**The starter has no sign-in and never reads the user.** How a site signs people in is its own
choice. A site that wants the user on its pages puts it in `context.page` once, in
`AppPage.handle_request()`: with Django's `AuthenticationMiddleware`, from
`await request.auser()` (`rendering_pipeline.md` says why that, and when `request.user` is fine
instead). The home page links to the example apps.
[`01_movie_manager`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager)
has a real sign-in: a custom `User` model, a Django Ninja sign-in endpoint called with `fetch`,
and the user on `AppState`.

## URLs for the frontend

**A controller never writes a path.** The `AppUrls` widget, rendered by the document template,
assigns each URL the frontend needs to the TypeScript `AppUrls` class: pages and endpoints from
`reverse_template()`, which leaves a route's parameters as placeholders (`/api/greeting/{name}`)
for the controller to fill, and static files from `static()`. A new URL is one line in the
widget's dict and one declaration in `app-urls.ts`. See `reverse_template.md`.

`static_bundled_styles` is the reason a static file's URL goes through `AppUrls` too.
`<loading-spinner>` is a web component, and a shadow root doesn't see the page's stylesheets, so
it imports the bundled stylesheet itself, `@import url("${AppUrls.static_bundled_styles}")`. A
versioning static storage gives a rebuilt stylesheet a new URL through `static()`; a path written
into TypeScript never changes, and browsers keep serving their stale copy.

## The endpoint

`GreetingEndpoint` is a plain Django class-based view with an `async def get()` returning a
`JsonResponse`, routed in the app's `urls.py`. **The package is REST-library agnostic**: it
renders pages and widgets, and has no endpoint class of its own. Endpoints written with Django
REST Framework, Django Ninja or anything else are called from a controller the same way, through
a URL in `AppUrls`. The starter's sleeps half a second so the spinner can be seen; delete that.

## The build files

`webpack.config.js`, `tsconfig.json` and `package.json` are the developer's to change, and most
sites will. Separate bundles per section, for instance, so no page loads another section's code:

```js
entry: {
  main_website: './ts/main_website.ts',
  main_reports: './ts/main_reports.ts',
},
output: {
  filename: '[name].js',
  ...
},
```

`ww_upgrade` still compares the first two with the installed package's versions, so a project
can take an improvement: one that differs is replaced only on a yes, after an optional diff. It
never edits `package.json`, which holds the project's own dependencies too; it prints the
`npm install --save-dev` command for any build tool missing or declared below the starter's
minimum, and any missing `build` or `watch` script. See `creating_and_upgrading_an_app.md`.

The webpack config keeps the module output templates import from, a content hash in lazily
loaded chunk names (webpack's runtime requests them by a URL the static storage can't rewrite),
and one extracted stylesheet, each explained in a comment there. Production builds minify class
names, so nothing may rely on `constructor.name`.

## No nonce

Nothing in the starter mentions a CSP nonce, since whether a site sends a Content Security
Policy is its own decision. A site that does adds the nonce to its document template and its
`<script>` tags, and to `ww_create_page`'s templates through `templates_dir`.
