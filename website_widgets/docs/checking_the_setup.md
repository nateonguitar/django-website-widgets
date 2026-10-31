# Checking the Setup

The package's system checks catch a website app that is set up wrong at the next `runserver`,
and `python manage.py ww_doctor` checks everything else a working frontend needs. Read this when
a page 404s that shouldn't, a controller doesn't run, or a check's id appears in the output.

Primary code:
- `website_widgets.page_routes.PageRoutes` — the routing checks
- `website_widgets.management.framework_folder.FrameworkFolder.check_version_stamp` — the out-of-date check
- `website_widgets.management.commands.ww_doctor` — the checklist
- `website_widgets.management.package_json_check.PackageJsonCheck` — the `package.json` check `ww_doctor` and `ww_upgrade` share

## The system checks

They run with every management command, as Django's own do, so they stay cheap: no
subprocesses, no network.

| Id | Fails when | Fix |
| --- | --- | --- |
| `website_widgets.E001` | two equally specific routes can match the same URL | see `routing.md` |
| `website_widgets.E002` | the project root holds the website app's folder (one with an `apps.py`, as `ww_create_app` writes it), but the app isn't in `INSTALLED_APPS` | add it to `INSTALLED_APPS` |
| `website_widgets.E003` | the website app has pages with `@register_url`, but no URL pattern includes `PageRoutes.urls()`, so all of them would 404 | `path('', include('<app>.urls'))`, or `path('', PageRoutes.urls())` |
| `website_widgets.W001` | a managed folder, `website_widgets_docs/` or `ts/website_widgets/`, is from another package version than the installed one | `ww_upgrade`, see `creating_and_upgrading_an_app.md` |

E002 and E003 catch the next steps `ww_create_app` prints and leaves to the developer, so a
skipped one fails with its fix instead of as a 404. Both stay quiet for a project using only the
Python half: E002 without the app folder, E003 without pages. E003 looks for the website app's
namespace among the project's URL namespaces, so it finds `PageRoutes.urls()` included directly or
through the app's own `urls.py`.

## `ww_doctor`

Everything a system check shouldn't do on every command, as a checklist in the style of
`flutter doctor`: a line per check, and under each failing one, how to fix it.

```
Checking the setup for django-website-widgets 0.10.2:
[✓] The package's system checks pass
[✓] The website app 'website' is installed, at website/
[✗] node is not on the PATH, so nothing builds the TypeScript or SCSS
    Install Node.js 18.12.0 or newer, which includes npm: https://nodejs.org
    Without Node on this machine, node_and_package_managers.md shows the build in a docker or podman container
[✗] No JavaScript package manager is installed (npm, yarn, pnpm), so nothing installs or builds the frontend
...
```

In order:

1. **The package's system checks**, each failing one with its hint. `ww_doctor` skips Django's
   own run of the checks before a command, so it can report them rather than stop on them.
2. **The website app is installed.** Without it, the checks on its folder are skipped. When
   E002 has already said the app isn't installed, this line is left out rather than say it twice.
3. **`node` is on the `PATH`,** at least 18.12, which webpack-cli 6 needs.
4. **A JavaScript package manager is on the `PATH`:** npm, yarn or pnpm, checked in that order.
   yarn or pnpm with no npm passes, noting that `start_npm_watch()` runs npm, so the project's
   watcher is its own. With none, the fixes are installing Node or building in a container
   (`node_and_package_managers.md`).
5. **`package.json` has what the starter site's build needs**, the same check `ww_upgrade` runs
   (below).
6. **`node_modules/` holds each build tool**, so `npm install` has run.
7. **The bundle is built:** Django's static finders find `main.js` and `bundled-styles.css`, the
   names the starter's webpack config writes and the templates load.

It ends with the number of problems found, and exits with status 1 when there are any, as
`makemigrations --check` does, so a script or CI job can stop on it.

It exists for a newcomer's broken setup, where "my controller doesn't run" turns out to be npm
missing from a container, and for an AI assistant helping them: one command reports everything.

## The `package.json` check

Each build tool the starter site's `package.json` lists must be declared, in `devDependencies`
or `dependencies`, with a range whose minimum is at least the starter's (`^5.97.1` is below
`^5.110.2`). A range with no version to compare, such as `latest` or a git URL, passes. The
`build` and `watch` scripts must exist, since a build and `start_npm_watch()` run them. The check
never edits the file: it prints `npm install --save-dev <name>@<range> ...` for the tools, and
the line to add for each script.
