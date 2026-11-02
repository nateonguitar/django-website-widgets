# Frontend Controllers

The framework's TypeScript: `Controller`, the base class of every page and widget controller,
`App`, which starts controllers and holds the singleton registry, `Completer`, and
`DialogController`, the base of a dialog its caller awaits. Read this before writing a
controller or a dialog, or when two controllers need to talk to each other.

Primary code, the npm package `django-website-widgets`, which the app's `package.json` depends
on and its controllers import from (`import { Controller } from "django-website-widgets"`). Its
sources ship beside the compiled code, in the app's `node_modules/django-website-widgets/src/`:
- `controller.ts` — `Controller`
- `app.ts` — `App`: `initController()`, `registerSingleton()`, `getSingleton()`
- `completer.ts` — `Completer`
- `dialog-controller.ts` — `DialogController`: `openDialog()`, `answer()`, `closesOnBackdropClick`, `saving`

## The code belongs to the package

**The framework's TypeScript is a dependency, not project code.** It comes from npm, at the range
the installed Python package works with (`creating_and_upgrading_an_app.md`), so an upgrade is a
version change, never an edit. A project changes behaviour by subclassing `Controller` or `App`
in its own files. A project's own frontend state, such as the logged-in user or feature flags,
lives in its own classes, never on `App`.

**A bundle holds one copy of the package.** `App` keeps the singleton registry on the class, so
two copies would mean two registries, and a controller registered in one could never be found
from the other. The app's `package.json` depends on it once; npm installs one copy.

## A controller's lifecycle

A widget's template starts its controller from a `<script type="module">` that imports `App`
and the controller from the bundle, and hands `App.initController()` a new controller and the
selector of the widget's root element:

```django
<div id="my-widget" class="my-widget" data-label="{{ data.label }}">…</div>

<script type="module">
    import { App, MyWidgetController } from '{% static "main.js" %}';
    await App.initController(new MyWidgetController(), '#my-widget');
</script>
```

**The template is the one place a selector is chosen,** a few lines from the root it names, so
the two can't drift apart unseen. A widget shown once has an id on its root and passes
`'#my-widget'`. A widget shown several times on a page takes a keyword-only `key` in its
constructor (`MovieCard(movie=movie, key=movie.id)`), keeps one class on every root, puts the key
in `data-key`, and passes a selector for it: `'.movie-card[data-key="{{ data.key }}"]'`, as
`ww_create_widget --repeating` writes it. Ids stay free for what they are for: labels, ARIA
references, anchors. Each root gets one controller; nothing in `App` is kept per
class except singletons, so each instance is independent. A controller with no element, such as
one that only watches the window, is started with no selector, `App.initController(new
ThemeController())`, and gets no DOM binding: `rootElement` stays `null`, while the lifecycle and
the singleton registry work as for any other. The caller constructs the controller, so its
constructor can take arguments.

`App.initController(controller, selector)`:

1. when a selector is given and an element matches it, binds the two: the controller's
   `rootElement` is the element, and the element's `__controller` is the controller, so the
   controller can be reached from its element, in the console or a browser test. When no
   element matches, nothing is bound and a warning names the controller and its selector, since
   a controller that was meant to have an element silently does nothing without one;
2. awaits `initState()`;
3. registers the controller as a singleton, when its class says `static readonly singleton = true`;
4. calls `setState()`;
5. calls `afterFirstSetState()`.

So `initState()` looks elements up and adds listeners, and never calls `setState()` itself,
since `App` calls it next. There is no teardown hook: nothing watches for a root leaving the
page, and a hook that never fires would invite cleanup code that never runs.

**State drives the DOM.** A controller keeps state in fields, an event handler only changes them
and calls `setState()`, and `setState()` writes the whole DOM from the fields. A DOM change made
in an event handler is lost or contradicted by the next `setState()`.

**A controller's shape,** as `ww_create_page` and `ww_create_widget` write it:

- **DOM references live on a module-level `class Elements`**, held as
  `private elements = new Elements()`, each field typed `HTMLElement | null = null`, since a lookup
  can find nothing. The controller's own fields are state only, so `this.loading` and
  `this.elements.submitButton` can't be confused.
- **`Elements` finds its own fields, in `findIn(root)`**, which `initState()` calls once with
  `this.rootElement`, and everything else reads them from `this.elements`. The class that names
  the elements is the one that knows their selectors, so the template's contract with the
  controller is in one place. `findIn()` returns at once when the root is `null`; after that,
  `querySelector()` already answers `null` for a missing element, so no fallbacks are needed.
  The field's declaration is the only place its type is written: `this.saveButton =
  root.querySelector('.editor__save')` takes `HTMLButtonElement` from the field, so the call
  needs no `<HTMLButtonElement>`, and `Array.from(root.querySelectorAll(...))` likewise takes its
  element type from an array field. Writing it on the call too checks nothing (neither form
  confirms the element really is a button) and can drift from the field. A lookup kept in a
  local variable, outside `Elements`, has no field to take a type from and still needs one.
  Looking inside the root keeps each instance to its own. Everything the controller touches is
  found there, including lists such as a form's submit buttons, so no render looks anything up
  again.
- **A base controller's `Elements` is exported and named for it,** such as
  `DialogControllerElements`, so a subclass imports it from the base's file, extends it with its
  own fields, and overrides `findIn()`, calling `super.findIn(root)` first. A controller nobody
  extends keeps a plain, unexported `Elements`. `initializeListeners()` is `protected`: a subclass
  may override it, and other controllers have no business calling it.
- **Data for one element is a `data-` attribute on the controller's root**, read from
  `this.rootElement.dataset`, not from child elements, hidden inputs or inline JSON. Data every page
  shares, such as the signed-in user, is on a project-owned state class the document template
  fills, such as the starter site's `AppState`.

**Which element lookup.** `this.rootElement.querySelector()`, so a controller finds only what
its own template rendered, and an element it needs sits inside its root. A lookup that finds
nothing returns `null`, and the controller checks for that where the template renders the element
only sometimes. Bind a listener on the element already found,
`this.elements.saveButton?.addEventListener('click', handler)`, rather than looking it up again.

## Singletons and readiness

Two controllers on one page talk through the singleton registry. A class declares itself one
with `static readonly singleton = true`, which `App.initController()` reads and registers, and
the other fetches it with `App.getSingleton(ChildController)`, which returns `null` when none is
registered. It's on the class, not an option at each call, since the code that relies on it is
elsewhere: a template that forgot the option would leave every `getSingleton()` call `null`.

**The registry is keyed on the class itself, not its name.** Production builds minify class
names (`class u extends c`), so two controllers can share a `constructor.name`. Nothing in the
framework is keyed on `constructor.name` or `Class.name`, and nothing in a project should be; the
no-element warning only prints it, beside the selector, which survives minifying.

Controllers start concurrently, each from its own `<script>`, and a singleton is only registered
after its `initState()`. So the controller asking for it may run first. The child signals that
it is ready with a `Completer`, a promise resolved from outside:

```typescript
export class ChildController extends Controller {
    static readonly singleton = true;
    public static singletonInitializationCompleter = new Completer<null>();

    public afterFirstSetState(): void {
        ChildController.singletonInitializationCompleter.resolve(null);
    }
}

// In the parent's initState():
await ChildController.singletonInitializationCompleter.promise;
const child = App.getSingleton(ChildController);
```

A `Completer` completes once: a second `resolve()` or `reject()` throws. `isCompleted` says
whether it has.

## Dialogs

**A dialog is something its caller awaits,** as Flutter's `showDialog` is: the caller shows it
and reads the answer on the next line, instead of passing callbacks.

```ts
const takeTheRest = await ConfirmDialogController.show({ message: 'Take the rest?' });
if (!takeTheRest) return;
```

`python manage.py ww_create_dialog <name>` writes a new dialog's widget, template and controller
(`creating_pages_and_widgets.md`). A controller opens a dialog from its own code, as above. A
page or widget without a controller opens one from a module `<script>` in its template, which
imports the dialog's controller from the bundle like any other:

```django
{% load static %}
{{ children.welcome_dialog }}

<script type="module">
    import { WelcomeDialogController } from '{% static "main.js" %}';
    await WelcomeDialogController.show();
</script>
```

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

**The controller extends `DialogController<R>`,** `R` being what the caller gets back. Its
static `show()` builds a controller from what it shows and hands it to `openDialog()` with the
template's selector, the same argument order as `App.initController()`:

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
without an answer wasn't answered no. Nothing resolves the promise except the `close` listener.

**The template's attributes the dialog reads:**

| On | Attribute | Does |
| --- | --- | --- |
| the `<template>` | `data-dialog-class` | the `<dialog>`'s classes, for its styles (width, padding, `::backdrop`) |
| an element inside | `data-dialog-label` | names the dialog for a screen reader (`aria-labelledby`) |
| a button inside | `data-dialog-close` | closes the dialog with no answer |

They are data attributes, so the package claims no class names in a project's CSS. The
`<dialog>` is otherwise bare, as Flutter's is: a box the content fills, styled by the project.

**The dialog decides how it can be dismissed, never its caller.** `closesOnBackdropClick`
(true by default) is set by a dialog a stray click would wipe, such as a form, to false. Such a
dialog needs its own way out, a Cancel or a `[data-dialog-close]` button, or Escape is the only
one. `saving`, set by a dialog around a request it sends, holds Escape, the backdrop and the
close buttons off until the request finishes.

**A browser quirk:** Chrome treats a modal opened without a click (one shown from a timer, say)
as one group with the modal under it, so a single Escape closes both. Each still answers its own
caller; the backdrop and close buttons close only the top one.

## What `Controller` leaves to the project

`Controller` only deals with the DOM. Anything a project has an opinion about stays out of it,
so the framework doesn't impose that opinion:

- **No logging.** It calls `console.warn` only for a real problem, such as a selector that
  matches nothing. A project that wants logging declares a label in each
  class and calls its own logger. `logInfo`/`logWarn`/`logError` helpers on `Controller` were
  tried and removed: they chose the logger for the project, and labelled messages with
  `this.constructor.name`, which a production build minifies to a letter or two.
- **No network method.** A `Controller.fetch()` was tried and moved out, because the HTTP client
  is the project's choice (plain `fetch`, axios, a wrapper of its own).
- **No state.** `App` holds only the framework's mechanics.
- **No CSP nonce.** Whether a site sends a Content Security Policy is its own security decision,
  so nothing the package ships mentions a nonce. A project that uses one adds it to its own
  `<script>` tags.
