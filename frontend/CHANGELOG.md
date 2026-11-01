# Changelog

Each release of the npm package, newest first. Versions follow
[semantic versioning](https://semver.org/). The Python package keeps its own changelog, in the
repository root, and declares which range of this package it works with.

## 1.0.0-rc.2

- **`DialogController<R>`, a dialog its caller awaits,** as Flutter's `showDialog` is:
  `const takeTheRest = await ConfirmDialogController.show({...})`. A dialog's widget renders its
  content in a `<template>`; `openDialog(controller, templateSelector)` creates a bare `<dialog>`
  around a copy of it, opens it, and resolves with the subclass's `answer()` once it closes.
  Each call gets its own dialog, controller and promise. The template marks the dialog's classes
  (`data-dialog-class`), its accessible name (`data-dialog-label`) and its close buttons
  (`data-dialog-close`); `closesOnBackdropClick` and `saving` are the dialog's to set.

## 1.0.0-rc.1

The first release. `Controller`, `App` and `Completer` move here from the TypeScript that
`ww_upgrade` copied into each website app's `ts/website_widgets/`, unchanged, so a project imports
them from `django-website-widgets` instead of from that folder.
