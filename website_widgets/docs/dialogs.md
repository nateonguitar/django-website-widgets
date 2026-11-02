# Dialogs

A dialog its caller awaits, on the npm package's `DialogController`: what its widget renders,
how `show()` opens it, how it answers and how it can be dismissed. Read this before writing or
opening a dialog; `frontend_controllers.md` covers the controller lifecycle it builds on.

Primary code, in the npm package `django-website-widgets`:
- `dialog-controller.ts` — `DialogController`: `openDialog()`, `answer()`, `closesOnBackdropClick`, `saving`

## Awaiting a dialog

**A dialog is something its caller awaits,** as Flutter's `showDialog` is: the caller shows it
and reads the answer on the next line, instead of passing callbacks.

```ts
const takeTheRest = await ConfirmDialogController.show({ message: 'Take the rest?' });
if (!takeTheRest) return;
```

`python manage.py ww_create_dialog <name>` writes a new dialog's widget, template and controller
(`creating_pages_and_widgets.md`). A controller opens a dialog from its own code, as above. A
page or widget without a controller opens one from a module `<script>` in its template:

```django
{% load static %}
{{ children.welcome_dialog }}

<script type="module">
    import { WelcomeDialogController } from '{% static "main.js" %}';
    await WelcomeDialogController.show();
</script>
```

## The widget renders a `<template>`

**The dialog's widget renders only a `<template>` holding its content,** with no `<dialog>`,
no ids and no `<script>`. A `<template>` is parsed but never shown and runs nothing, so it costs
nothing on a page that never opens it. It is placed like any other child: in the page that can
show it, or in the document template when every page can (a confirm).

```django
<template id="confirm-dialog-template" data-dialog-class="confirm-dialog">
  <p class="confirm-dialog__message" data-dialog-label></p>
  <button type="button" class="confirm-dialog__no">No</button>
  <button type="button" class="confirm-dialog__yes">Yes</button>
</template>
```

| On | Attribute | Does |
| --- | --- | --- |
| the `<template>` | `data-dialog-class` | the `<dialog>`'s classes, for its styles (width, padding, `::backdrop`) |
| an element inside | `data-dialog-label` | names the dialog for a screen reader (`aria-labelledby`) |
| a button inside | `data-dialog-close` | closes the dialog with no answer |

They are data attributes, so the package claims no class names in a project's CSS. The
`<dialog>` is otherwise bare: a box the content fills, styled by the project.

## The controller

**The controller extends `DialogController<R>`,** `R` being what the caller gets back. Its
static `show()` builds a controller and hands it to `openDialog()` with the template's selector,
the same argument order as `App.initController()`:

```ts
import { DialogController } from "django-website-widgets";

export class ConfirmDialogController extends DialogController<boolean | null> {
    private chosen: boolean | null = null;

    constructor(private message: string) {
        super();
    }

    public static show({ message }: { message: string }): Promise<boolean | null> {
        const controller = new ConfirmDialogController(message);
        return DialogController.openDialog(controller, '#confirm-dialog-template');
    }

    // initState(), setState() and the button listeners as in any controller; a button calls:
    private choose(chosen: boolean): void {
        this.chosen = chosen;
        this.dialog?.close();
    }

    protected answer(): boolean | null {
        return this.chosen;
    }
}
```

`openDialog()` creates a bare `<dialog>`, copies the template's content into it, gives it the
classes in `data-dialog-class`, starts the controller on it, and opens it with `showModal()`.
The controller reaches the element as `this.dialog`, typed `HTMLDialogElement`. When the dialog
closes, however it closes, the one `close` listener resolves the caller's promise with
`answer()` and removes the element. Every call gets its own element, controller and promise, so
two dialogs shown back to back, or one over another, never get each other's answers.

**Whatever produces the result stores it, then closes.** A button's choice, a saved form's
record: each goes in a typed field, then `this.dialog.close()`, and `answer()` returns the field.
Escape, a click on the backdrop and a `[data-dialog-close]` button close the dialog with nothing
stored, so the field's starting value is the answer to a dismissal: `null`, since a dialog left
without an answer wasn't answered no.

## Dismissal

**The dialog decides how it can be dismissed, never its caller.** `closesOnBackdropClick`
(true by default) is set to false by a dialog a stray click would wipe, such as a form; it then
needs its own way out, a Cancel or a `[data-dialog-close]` button, or Escape is the only one.
`saving`, set around a request the dialog sends, holds Escape, the backdrop and the close
buttons off until the request finishes.

**Worked example:** the movie manager example's `ReportCopyDialog`
([`website/widgets/report_copy_dialog/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager/website/widgets/report_copy_dialog))
is a form dialog: backdrop clicks ignored, `saving` around its request, field errors from a 400
beside their fields, and the saved report as its answer. Its `ConfirmDialog` is the yes-or-no
case.

**A browser quirk:** Chrome treats a modal opened without a click (one shown from a timer, say)
as one group with the modal under it, so a single Escape closes both. Each still answers its own
caller; the backdrop and close buttons close only the top one.
