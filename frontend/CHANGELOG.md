# Changelog

Each release of the npm package, newest first. Versions follow
[semantic versioning](https://semver.org/). The Python package keeps its own changelog, in the
repository root, and declares which range of this package it works with.

## 1.0.0-rc.1

The first release. `Controller`, `App` and `Completer` move here from the TypeScript that
`ww_upgrade` copied into each website app's `ts/website_widgets/`, unchanged, so a project imports
them from `django-website-widgets` instead of from that folder.
