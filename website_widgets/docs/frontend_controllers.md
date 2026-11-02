# Frontend Controllers

The framework's TypeScript: `Controller`, the base of every page and widget controller, `App`,
which starts controllers and holds the singleton registry, and `Completer`. Read this before
writing a controller, or when two controllers need to talk to each other. A dialog's
`DialogController` builds on this, in `dialogs.md`.

Primary code, the npm package `django-website-widgets`, which the app's `package.json` depends
on and its controllers import from (`import { Controller } from "django-website-widgets"`). Its
sources ship beside the compiled code, in the app's `node_modules/django-website-widgets/src/`:
- `controller.ts` — `Controller`
- `app.ts` — `App`: `initController()`, `registerSingleton()`, `getSingleton()`
- `completer.ts` — `Completer`

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
`'#my-widget'`. A widget shown several times takes a keyword-only `key`
(`MovieCard(movie=movie, key=movie.id)`), keeps one class on every root, puts the key in
`data-key`, and passes `'.movie-card[data-key="{{ data.key }}"]'`, as `ww_create_widget
--repeating` writes it; ids stay free for labels, ARIA references and anchors. Each root gets its
own controller. A controller with no element, such as one that only watches the window, is
started with no selector (`App.initController(new ThemeController())`) and keeps `rootElement`
`null`. The caller constructs the controller, so its constructor can take arguments.

`App.initController(controller, selector)`:

1. when an element matches the selector, binds the two: `rootElement` is the element, and the
   element's `__controller` is the controller (reachable in the console or a browser test). When
   none matches, a warning names the controller and its selector;
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
- **`Elements` finds its own fields inside the root, in `findIn(root)`**, which `initState()`
  calls once with `this.rootElement`. The class that names the elements knows their selectors,
  so the template's contract with the controller is in one place, and looking inside the root
  keeps each instance to its own. Everything the controller touches is found there once, lists
  included; nothing is looked up again later, and a listener is bound on the element already
  found (`this.elements.saveButton?.addEventListener(...)`). `findIn()` returns at once when the
  root is `null`, and a missing element is simply `null`, which the controller checks where the
  template renders it only sometimes.
- **The field's declaration is the only place its type is written.** `this.saveButton =
  root.querySelector('.editor__save')` and `Array.from(root.querySelectorAll(...))` take their
  types from the fields; a `<HTMLButtonElement>` on the call checks nothing and can drift. A
  lookup in a local variable, having no field, still needs one.
- **A base controller's `Elements` is exported and named for it,** such as
  `DialogControllerElements`, so a subclass imports it from the base's file, extends it with its
  own fields, and overrides `findIn()`, calling `super.findIn(root)` first. A controller nobody
  extends keeps a plain, unexported `Elements`. `initializeListeners()` is `protected`: a subclass
  may override it, and other controllers have no business calling it.
- **Data for one element is a `data-` attribute on the controller's root**, read from
  `this.rootElement.dataset`, not from child elements, hidden inputs or inline JSON. Data every page
  shares, such as the signed-in user, is on a project-owned state class the document template
  fills, such as the starter site's `AppState`.

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

## What `Controller` leaves to the project

`Controller` only deals with the DOM; anything a project has an opinion about stays out of it:

- **No logging.** It calls `console.warn` only for a real problem, such as a selector that
  matches nothing. A project that wants logging declares a label string in each class and calls
  its own logger; `this.constructor.name` is no label, since a production build minifies it.
- **No network method.** The HTTP client is the project's choice (plain `fetch`, axios, a
  wrapper of its own).
- **No state.** `App` holds only the framework's mechanics.
- **No CSP nonce.** Whether a site sends a Content Security Policy is its own decision, so
  nothing the package ships mentions a nonce. A project that uses one adds it to its own
  `<script>` tags.
