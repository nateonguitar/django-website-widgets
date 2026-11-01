# Development Guide

## Setup

The library needs only Python 3.12+ and Poetry. From the repository root:

```bash
poetry install --no-root
```

This creates a virtualenv with Django, at the version pinned in `poetry.lock`. The lock file pins
the development environment only; a project installing the package gets any Django that
`pyproject.toml` allows.

## Tests

```bash
poetry run django-admin test website_widgets --settings=test_settings --pythonpath=.
```

`test_settings.py` sits at the repository root, outside the package, so it never ships. Every test
is a `SimpleTestCase`, so it configures no database. It does configure a `DjangoTemplates` backend,
because widget templates are compiled with `Template()`, which raises `ImproperlyConfigured`
without one. Any project using the library has one already.

**One test class per file, named for what it tests.** A class's tests sit in a folder named for
the module (`tests/widget/test_render.py` for a widget's `render()`,
`tests/page_routes/test_register_url.py`); a module with one test class keeps a flat
`tests/test_<module>.py`. Test names follow `test_<feature>__<succeeds/fails>__when_<condition>`.
The shared pieces sit beside the tests:

- `tests/sample_widgets.py`: the widgets and pages the tests render.
- `tests/widget_test_case.py`: `WidgetTestCase.write_template()`, which writes a test's template
  beside `sample_widgets.py`, since a widget's template is looked up beside its class's module.
- `tests/urls.py`: the URLconf `reverse_template()` is tested against, also `ROOT_URLCONF`.
- `tests/page_routes/page_routes_test_case.py`: an empty route registry and a throwaway website
  app for each test.

GitHub Actions (`.github/workflows/tests.yml`) runs the same command on every push, for each
supported Python against each supported Django. **Supporting a new Django or Python version means
adding it to the matrix and the classifiers in `pyproject.toml` together**, and dropping one means
removing it from both, along with `requires-python` or the `django` requirement when the lowest
version changes.

## Examples

`examples/` holds Django projects that show the library in use, numbered in reading order.
`01_movie_manager` is the main one, built the way the package means a site to be: created by
`ww_create_app`, with TypeScript, SCSS and webpack. `02_animal_shelter` is the tiny no-build one,
needing only Poetry. A technique too narrow for either is a lesson in `website_widgets/docs/`,
which ships, rather than another project. `examples/README.md` is the reader's index; keep it in
step when one is added.

- **Each is its own project:** its own `manage.py`, settings and `pyproject.toml`, so one folder
  copies out as the start of someone's site. Each depends on the package by relative path,
  `django-website-widgets = {path = "../..", develop = true}`, so it runs the code in this
  checkout, and a package change shows up in every example at once.
- **The movie manager starts from the package's own commands.** `startproject`, `ww_create_app`,
  then `ww_create_page` and `ww_create_widget` for each page and widget, committed exactly as
  they came out before any hand work, so its history diffs what the package generates against
  what a developer writes. Something every generated file needs corrected by hand is a bug in a
  command, fixed here.
- **They run on models and SQLite**, seeded by a data migration, so `migrate` alone gives a
  working site and every test starts from the same rows. `db.sqlite3` is git-ignored.
- **Run one:** `cd examples/02_animal_shelter`, `poetry install`,
  `poetry run python manage.py migrate`, then `runserver` or `test`. The movie manager also needs
  `npm ci` in `frontend/` once, then `npm install` in its `website/` folder; its README says so.
  It depends on `frontend/` by path, and npm builds that with `frontend/`'s own TypeScript.
- **CI runs every example's tests**, finding each folder with a `manage.py`, so a new example needs
  no workflow edit. An example that a package change breaks fails the build like a package test.
  An example with a `package.json` in its website app also gets `npm ci`, a type-check and a
  production build, since its Python tests never compile its TypeScript or SCSS; commit its
  `package-lock.json`, which `npm ci` installs from.
- **They never ship.** `exclude` in `[tool.poetry]` keeps `examples/` out of the wheel and the
  source archive.

## Releasing

A change reaches a project using the library only through a published version. The library is
two packages with one name: `django-website-widgets` on PyPI (the Python package) and on npm
(`frontend/`, the TypeScript a project's controllers import). **They are versioned separately**,
and each is released only when it changed.

**The Python package declares the npm range it works with**, `NpmPackage.RANGE`
(`website_widgets/management/npm_package.py`), which
`ww_create_app` writes into a new app's `package.json`, `ww_upgrade` sets there after an upgrade,
and a system check and `ww_doctor` compare with what is installed. Raise it when the Python side
starts relying on something only a newer npm release has: a new export, a data attribute both
halves read. Then release the npm package first, and the Python package declaring the new range
second, so the range never names a version that isn't published.

### The Python package

1. Bump `version` in `pyproject.toml`, following semantic versioning from 1.0 on: a breaking
   change needs a new major version.
2. Add the version's entry at the top of `CHANGELOG.md`: what changed, and for each breaking
   change, what a project changes to upgrade. A release candidate's entry is written as the
   final version's.
3. Run the tests, and check the GitHub Actions matrix is green.
4. Build with `poetry build`, then check that nothing but the package ships: both commands must
   print nothing.
   ```bash
   unzip -Z1 dist/*.whl | grep -vE '^website_widgets/|\.dist-info/' ; unzip -Z1 dist/*.whl | grep '/tests/'
   tar tzf dist/*.tar.gz | sed 's|^[^/]*/||' | grep -vE '^(website_widgets/|$|README.md|LICENSE|pyproject.toml|PKG-INFO)' ; tar tzf dist/*.tar.gz | grep -E '/tests/|/examples/'
   ```
   `exclude` in `[tool.poetry]` keeps `website_widgets/tests/` and `examples/` out.
5. Publish with `poetry publish`. Publishing needs a PyPI token, set once with
   `poetry config pypi-token.pypi <token>`.
6. Tag the release (`git tag v1.0.0`) and push the tag.
7. Bump the requirement in the project using it.

`poetry build` writes the wheel and source archive to `dist/`, which is git-ignored.

### The npm package

Run these in `frontend/`, with Node and npm on the host.

1. Bump `version` in `frontend/package.json`, following semantic versioning; a release candidate
   is `1.0.0-rc.1`, npm's spelling of Python's `1.0.0rc1`.
2. Add the version's entry at the top of `frontend/CHANGELOG.md`.
3. Run `npm run typecheck`, and check that CI's example builds, which install this folder, are
   green.
4. Check what would ship with `npm pack --dry-run`: `dist/` (built by the `prepare` script),
   `src/`, `README.md`, `CHANGELOG.md`, `LICENSE` and `package.json`, nothing else.
5. Publish with `npm publish`, adding `--tag next` for a release candidate so it doesn't become
   what a bare `npm install django-website-widgets` gets. npm asks for the two-factor code.
6. Tag the release with a prefix, so it can't be mistaken for a Python release
   (`git tag npm-v1.0.0`), and push the tag.
7. If the Python package should require it, raise `NpmPackage.RANGE` and release the Python
   package.

`npm run build` writes `frontend/dist/`, and `npm install` writes `frontend/node_modules/`; both
are git-ignored. `frontend/package-lock.json` is committed, pinning the TypeScript that builds it.

## Package structure

```
django-website-widgets/
├── pyproject.toml              # Package metadata and build config
├── poetry.lock                 # The development environment's pins
├── test_settings.py            # Settings for the tests, not shipped
├── .github/workflows/          # The test matrix and the examples' tests
├── examples/                   # Runnable example projects, not shipped; see "Examples"
├── frontend/                   # The npm package: src/ (App, Controller, Completer, index.ts),
│                               # its own package.json, README and CHANGELOG; see "Releasing"
├── README.md                   # The introduction (shows on PyPI), linking to the docs
├── CHANGELOG.md                # Each release from 1.0.0, with how to upgrade; not shipped
├── DEVELOPMENT.md              # This file
├── LICENSE
└── website_widgets/            # The Python package, the only thing shipped (minus tests/)
    ├── docs/                   # How each part works, and why, indexed by docs/AGENTS.md
    ├── docs_folder_README.md   # The README of a project's copy of docs/
    ├── generator_templates/    # ww_create_page's and ww_create_widget's default templates (*.tmpl)
    ├── starter_site/           # The site ww_create_app writes, its build files included (*.tmpl)
    ├── __init__.py             # Exports AsyncWidget, SyncWidget, AsyncWebPage, SyncWebPage,
    │                           # WidgetContext, PageRoutes, register_url, reverse_template,
    │                           # start_npm_watch
    ├── apps.py
    ├── config.py               # WebsiteWidgetsConfig, GenerateComponentConfig, get_config()
    ├── py.typed                # Says the package's type hints are its public types (PEP 561)
    ├── widget.py               # AsyncWidget and SyncWidget, over their private _Widget
    ├── web_page.py             # AsyncWebPage and SyncWebPage, over their private _WebPage
    ├── page_routes.py          # @register_url, route discovery, the routing system checks
    ├── url_templates.py        # reverse_template()
    ├── npm_watch.py            # start_npm_watch(), for manage.py
    ├── widget_context.py
    ├── tests/                  # One test class per file, not shipped; see "Tests" above
    └── management/
        ├── framework_folder.py # FrameworkFolder and its managed folder, DocsFolder
        │                       # (<app>/website_widgets_docs/), and its out-of-date check
        ├── npm_package.py      # NpmPackage: the npm package's name and RANGE, the versions this
        │                       # release works with, and its installed-version check; NpmVersion
        ├── component_files.py  # ComponentFiles: the file work ww_create_page and ww_create_widget
        │                       # both call; each command's own handle() reads top to bottom
        ├── starter_site.py     # StarterSite: fills starter_site/ in for an app
        ├── build_files.py      # BuildFiles: ww_upgrade's handling of the build configs and package.json
        ├── package_json_check.py  # PackageJsonCheck: package.json against the starter's, for
        │                       # ww_upgrade and ww_doctor
        └── commands/           # ww_create_app, ww_upgrade, ww_create_page, ww_create_widget,
                                # ww_show_routes, ww_doctor
```

## Docs

**The docs live inside the Python package,** in `website_widgets/docs/`, so they ship in the wheel
and a project's installed copy carries the docs for its version. `AGENTS.md`, beside them,
indexes them, one line per doc, and `tests/test_agents_md.py` fails when a doc has no index line
or an index line names a doc that doesn't exist. A new doc gets its line in the same change, and
a README section that grows past an introduction moves into a doc with a link left behind. The
README's links are absolute GitHub URLs, since PyPI shows the README but not the files beside it.

**`ww_create_app` and `ww_upgrade` copy `docs/` into projects as it is,** flat, into the app's
`website_widgets_docs/`, so the docs are written for where they land: the framework TypeScript by
what the npm package exports, a doc by its bare filename, and Python by its dotted name
(`website_widgets.web_page`), never a repo path like `website_widgets/web_page.py`. The managed
folder's README is a template, `docs_folder_README.md`. `FrameworkFolder` fills in its
`{version}` and `{file_list}`, and the out-of-date check reads the version back, so keep its
"Copied from django-website-widgets {version} by" line.

**`generator_templates/` holds no project opinions**: no logging, no nonce, no HTTP client.
`tests/test_generator_templates.py` fails when one creeps in. They're named `*.tmpl`
and kept out of a `templates/` folder, so neither Python tooling nor Django's template loader
mistakes them for real files.

**`starter_site/` is the site `ww_create_app` writes**, every file a `*.tmpl` for the same reason,
at the path it lands at in the app. `StarterSite` fills `__app_label__`, `__AppConfigClass__`,
`__npm_package_name__` and `__npm_package_range__` (`NpmPackage.RANGE`). Unlike the generator templates it shows conventions (`AppState`, `AppUrls`,
calling an endpoint), but never a nonce. `tests/commands/test_starter_site.py` creates it, installs
it and serves it, so a broken starter fails the suite. Its TypeScript isn't type-checked here, since
the package has no Node toolchain: after changing it, build a fresh one (`ww_create_app` in a
scratch project, `npm install`, `npx tsc --noEmit -p .`, `npm run build`).

**The framework TypeScript is the npm package in `frontend/`.** Gametabs and every other project
depend on it from npm, at the range `NpmPackage.RANGE` declares; a change is made here and
reaches them in an npm release. The examples depend on this folder directly
(`file:../../../frontend`), so they always run both halves from the same commit.

**Every command is `ww_`-prefixed, and `ww_create_*` is the one verb for writing new files.**
A new command follows both, so `manage.py help`'s list and a project's shell history say where a
command comes from.

## Gotchas

**The distribution and import names differ.** The package is installed as
`django-website-widgets` and imported as `website_widgets`, so `[tool.poetry]` names the package
to include explicitly; without it Poetry looks for a `django_website_widgets` folder and builds an
empty wheel.
