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
`ww_show_routes`, `ww_doctor` and `ww_upgrade`.

A skipped first or second step fails a system check at the next command, rather than showing up
as a 404, and `ww_doctor` reports the rest; see `checking_the_setup.md`.

## `ww_upgrade`

Run it after every upgrade of the package, and once on an app that never ran `ww_create_app`,
such as one a site already had. The app has to be installed; the command stops with an error
naming the label when it isn't. It runs no system checks first, since it is the fix for the
stale-folder warning below, and a page module that fails to import mustn't stop it. It rewrites the managed folder, reports what changed, sets the npm
package's range and checks the build files (below), and offers the docs pointer.

**It never creates or touches any other starter file.** `document_template.html`, `AppPage`,
`exceptions.py`, `main.ts`, `app-state.ts`, `app-urls.ts`, the starter pages and the endpoint are
written once by `ww_create_app` and are the developer's from then on, so a site adopting the
package gets no demo files from an upgrade. To start from one, copy it from a fresh
`ww_create_app` in a scratch project.

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
included, so a doc names another by its bare filename in both places.

**The framework TypeScript is no longer copied.** Before 1.0.0rc3, `ww_upgrade` also wrote
`App`, `Controller` and `Completer` into `ts/website_widgets/`. They are the npm package now, and
an app that still has that folder keeps it until the developer deletes it: nothing manages it any
more, and imports of it move to `django-website-widgets` (the changelog has the steps).

**Each file the package ships is overwritten, and nothing else in the folder is touched.** The
README lists every file the package wrote. On the next run, a file on that list that the new
version no longer ships, such as a renamed doc, is deleted. A file that was never on the list,
such as one a developer added, is left alone, and so is a listed path that would reach outside
the folder.

`ww_upgrade` reports every file as added, changed or removed (the unchanged ones as a count),
and suggests committing the folder. A file that differs only in its line endings, as a Windows
checkout with git's `autocrlf` leaves it, counts as unchanged and isn't rewritten. Committed, an upgrade shows up as a git diff of exactly what
changed, and a developer who edited a copy anyway sees what was replaced.

**Don't edit the copies.** A project changes the framework's behaviour by subclassing
`Controller` or `App` in its own files, never by editing the npm package in `node_modules/`; see
`frontend_controllers.md`.

## The docs read from where they land

The copied docs are written for the project's tree, not the package repo's: the framework
TypeScript by what the npm package exports (`import { Controller } from "django-website-widgets"`),
a doc by its bare filename, and Python code by its dotted name
(`website_widgets.web_page.AsyncWebPage`), since both halves are installed rather than copied.
They're in the project because an installed package may live only inside a container, and an AI
assistant or a person should be able to read them without starting one.

## The docs pointer

After writing the folders, for each file AI coding assistants read instructions from, both
commands ask whether to append one line pointing them at the copied `AGENTS.md`. They look for
`CLAUDE.md`, `.claude/CLAUDE.md` (both read by Claude Code) and `AGENTS.md` (read by Codex, Cursor
and others), all relative to the project root, and ask once per file found:

```
- `website/website_widgets_docs/AGENTS.md` — how django-website-widgets works; read before changing pages, widgets or controllers
```

The path in the line is relative to the project root in every one of them, `.claude/CLAUDE.md`
included, since that's how paths in these files are read. Neither asks when the file already
names that path. A file still naming the pre-0.8.0 path, `<app>/ts/website_widgets/AGENTS.md`,
is asked instead whether to update it, which changes that path to the new one wherever the file
names it and adds no second line. A `CLAUDE.md` linked to `AGENTS.md` is one file, asked about
once. When none of the three exists, they offer to create `AGENTS.md` holding just that line. The
default answer is no. This is the only time either writes outside the app, and only on a yes.

The project root is `settings.BASE_DIR`, or the current directory without one; `--project-root`
names another.

## Options

- `--noinput` (or `--no-input`): `ww_create_app` writes without asking; neither adds a docs
  pointer, saying where one is missing. `ww_upgrade` still writes the docs folder, since its
  files are the package's, and the npm package's range, and keeps a build config that differs. Without `--noinput` and with no input
  to read, as in a script that forgot the flag, every question takes its default answer.
- `--project-root`: where `ww_create_app` creates the app, and where both look for `CLAUDE.md`,
  `.claude/CLAUDE.md` and `AGENTS.md`.

The package takes no position on how a project runs its commands. Files they write belong to
whoever ran them, so a container running as root writes root-owned files; that's the project's
to handle.
