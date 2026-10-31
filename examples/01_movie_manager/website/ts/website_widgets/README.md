# website_widgets frontend framework

Copied from django-website-widgets 0.11.0 by `python manage.py ww_upgrade` or `ww_create_app`.

**This folder is managed by the package: don't edit the files it wrote here** (listed below).
They're the framework TypeScript your controllers import, and running `ww_upgrade` after an
upgrade overwrites them. Commit this folder, so an upgrade shows up as a diff of exactly what
changed. A system check warns when this folder is from another version than the installed
package. The package's docs are in the app's other managed folder, `website_widgets_docs/`.

To change how something here behaves, subclass it in your own code: extend `Controller` for a
controller, or subclass `App` and use your subclass. Keep project state, such as the logged-in
user or feature flags, in your own classes rather than on `App`.

| File | Holds |
| --- | --- |
| `app.ts` | `App`: `initController()` and the singleton registry |
| `controller.ts` | `Controller`, the base class every page and widget controller extends |
| `completer.ts` | `Completer`, a promise resolved from outside, used to signal readiness |

Files the package wrote, which `ww_upgrade` overwrites, or deletes once the package stops shipping
them:

<!-- website_widgets:files -->
- `app.ts`
- `completer.ts`
- `controller.ts`
- `README.md`
<!-- /website_widgets:files -->
