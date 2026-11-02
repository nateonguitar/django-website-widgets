# Creating and Upgrading a Website App

`python manage.py ww_create_app` creates a new website app, holding a working starter site.
`python manage.py ww_upgrade` brings an existing one's framework files up to the installed
package, and is how a project takes a new version. Both write the app's managed folder,
`website_widgets_docs/` (the package's docs), the same way, and both point `package.json` at the
npm package `django-website-widgets`, the framework TypeScript the app's controllers import. Read
this before creating an app, before upgrading the package, or when a file in the docs folder or
the npm package's range changed and it isn't clear why.

Primary code:
- `website_widgets.management.commands.ww_create_app` and `website_widgets.management.commands.ww_upgrade` — the commands
- `website_widgets.management.framework_folder.FrameworkFolder` — what a managed folder is, and the system check on it; `DocsFolder` is the one there is
- `website_widgets.management.npm_package.NpmPackage` — the npm package's name and `RANGE`, the versions of it this Python release works with, and the system check on what is installed
- `website_widgets.management.starter_site.StarterSite` — the starter site `ww_create_app` writes
- `website_widgets.management.build_files.BuildFiles` — `ww_upgrade`'s handling of the build files
- `README.md` in each managed folder — what the folder is, the version it was copied from and the list of files the package wrote

## The app's name

**The app is `WebsiteWidgetsConfig.website_app_name`, `website` by default, and `ww_create_app`
takes no name.** The running site reads that setting too: route discovery imports
`<app>/pages/`, decorated pages reverse as `<app>:<name>`, and `start_npm_watch()` runs in the
app's folder. The package supports one website app per project, so an app created under any
other name would never be routed. To use another name, set it in `settings.py` first:

```python
from website_widgets.config import WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(website_app_name='storefront')
```

Without a `WEBSITE_WIDGETS`, `ww_create_app` says it is using the default name, and how to set
another, before it lists anything.

## `ww_create_app`

It lists every file it is about to write, then asks `Create these files? [y/N]`; `--noinput`
writes them without asking. It refuses when the app's folder exists or an app with that label is
installed, pointing at `ww_upgrade` instead. It writes, in the project root, the app's folder
holding the starter site (`starter_site.md` says what each file is for), its build files
(`package.json`, depending on the npm package at `NpmPackage.RANGE`, `webpack.config.js`,
`tsconfig.json`) and the managed folder (below).

Then it offers the docs pointer (below) and prints the next steps, each a one-line change it
leaves to the developer, since it never edits a file it didn't create:

1. the app in `INSTALLED_APPS`;
2. `path('', include('<app>.urls'))` in the project's `urls.py`, with `include` imported from
   `django.urls`, where the app's `urls.py` includes `PageRoutes.urls()` and routes the starter
   endpoint;
3. `start_npm_watch()` in `manage.py` (`npm_watch.md`);
4. `npm install` in the app's folder, for the npm package and the build tools;
5. `runserver`, and the home page.

It ends with the package's other commands, one line each: `ww_create_page`, `ww_create_widget`,
`ww_create_dialog`, `ww_show_routes`, `ww_doctor` and `ww_upgrade`.

A skipped first or second step fails a system check at the next command, rather than showing up
as a 404, and `ww_doctor` reports the rest; see `checking_the_setup.md`.

## `ww_upgrade`

Run it after every upgrade of the package, and once on an app that never ran `ww_create_app`.
The app has to be installed. It runs no system checks first, since it is the fix for the
stale-folder warning below and a page module that fails to import mustn't stop it. It rewrites
the managed folder, sets the npm package's range, checks the build files (below), and offers the
docs pointer.

**It never creates or touches any other starter file.** The starter's pages, templates,
TypeScript and endpoint are written once by `ww_create_app` and are the developer's from then on;
to start from one later, copy it from a fresh `ww_create_app` in a scratch project.

## The build files

| File | On `ww_upgrade` |
| --- | --- |
| `webpack.config.js`, `tsconfig.json` | Created when missing, since a build needs them. Skipped silently when identical to the starter site's. **When different, it asks** whether to replace it, defaulting to no; `d` shows the difference first. Under `--noinput` a different file is kept, and the output says so. |
| `package.json` | Created when missing. Otherwise **the one value it writes is the npm package's range**, set to `NpmPackage.RANGE` when it differs (added to `dependencies` when missing), changing nothing else in the file: it holds the project's own dependencies too. A spec naming a folder or git, as the examples' `file:` one does, is left alone. The rest is checked against the starter's, and the fixes are printed (`checking_the_setup.md`). Run `npm install` after a range change. |

The two configs get a question because the developer may have tuned them, while a newer package
version may ship a better default: asking per file lets a project take the improvement without
losing its changes.

**The npm package is versioned separately from the Python package**, each released when it
changes. The Python package declares the npm range it works with, `NpmPackage.RANGE`, raised
only when its side starts relying on something a newer npm release added.

**A system check warns when the managed folder is from another version than the installed
package** (`website_widgets.W001`), read from its README's version stamp, so a project that
upgrades the package and forgets `ww_upgrade` hears about it at the next `runserver`. **Another
warns when the installed npm package is outside `NpmPackage.RANGE`** (`website_widgets.W002`),
read from `node_modules/django-website-widgets/package.json`. Both are silent when the app, the
folder or `node_modules/` doesn't exist, since a site may use only the Python half.

## The managed folder

```
<app>/
└── website_widgets_docs/   the package's docs; nothing here is imported or served
    ├── AGENTS.md           the index of the docs beside it
    ├── routing.md, ...     the package's docs, this one included
    └── README.md           don't edit; the version and the list of files the package wrote
```

`website_widgets_docs/` is a flat copy of the package's own `docs/` folder, `AGENTS.md`
included, so a doc names another by its bare filename in both places. It is in the project
because an installed package may live only inside a container, and an AI assistant or a person
should be able to read the docs without starting one. Don't edit the copies.

**Each file the package ships is overwritten, and nothing else in the folder is touched.** The
README lists every file the package wrote; on the next run, a listed file the new version no
longer ships (a renamed doc) is deleted, while a file never on the list (one a developer added)
is left alone, as is a listed path that would reach outside the folder. `ww_upgrade` reports
every file as added, changed or removed and suggests committing the folder, so an upgrade shows
up as a git diff of exactly what changed. A file differing only in line endings (git's
`autocrlf`) counts as unchanged.

## The docs pointer

After writing the folders, for each file AI coding assistants read instructions from, both
commands ask whether to append one line pointing them at the copied `AGENTS.md`. They look for
`CLAUDE.md`, `.claude/CLAUDE.md` (both read by Claude Code) and `AGENTS.md` (read by Codex, Cursor
and others), all relative to the project root, and ask once per file found:

```
- `website/website_widgets_docs/AGENTS.md` — how django-website-widgets works; read before changing pages, widgets or controllers
```

The path is relative to the project root in every file, `.claude/CLAUDE.md` included. Neither
asks when the file already names it; a file naming the pre-0.8.0 path,
`<app>/ts/website_widgets/AGENTS.md`, is offered an update in place instead. A `CLAUDE.md`
linked to `AGENTS.md` is asked about once. When none of the three exists, they offer to create
`AGENTS.md` holding just that line. The default answer is no, and this is the only time either
writes outside the app.

## Options

- `--noinput` (or `--no-input`): `ww_create_app` writes without asking. Neither adds a docs
  pointer, saying where one is missing. `ww_upgrade` still writes the docs folder and the npm
  range, and keeps a build config that differs. With no input to read and no flag, as in a
  script, every question takes its default.
- `--project-root`: where `ww_create_app` creates the app and both look for `CLAUDE.md`,
  `.claude/CLAUDE.md` and `AGENTS.md`; `settings.BASE_DIR` by default, else the current
  directory.

Files the commands write belong to whoever ran them, so a container running as root writes
root-owned files; that's the project's to handle.
