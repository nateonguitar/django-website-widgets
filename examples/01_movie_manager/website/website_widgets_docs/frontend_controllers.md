# Frontend Controllers

The framework's TypeScript: `Controller`, the base class of every page and widget controller,
`App`, which starts controllers and holds the singleton registry, and `Completer`. Read this
before writing a controller, or when two controllers need to talk to each other.

Primary code, in the app's `ts/website_widgets/`:
- `controller.ts` — `Controller`
- `app.ts` — `App`: `initializeController()`, `registerSingleton()`, `getSingleton()`
- `completer.ts` — `Completer`
- `README.md` — the don't-edit notice, the package version and the list of files the package wrote

## The files belong to the package

**Never edit the framework's TypeScript files.** They are the package's code, copied into the
project by `ww_create_app` and `ww_upgrade` only because a bundler needs them in the project
tree. Running `ww_upgrade` after a package upgrade overwrites them, so an edit is lost; with the
folder committed, the diff shows what it replaced. A project changes behaviour by
subclassing `Controller` or `App` in its own files. A project's own frontend state, such as the
logged-in user or feature flags, lives in its own classes, never on `App`.

## A controller's lifecycle

A widget's template starts its controller from a `<script type="module">` that imports it from
the bundle, passing the selector of the widget's root element:

```django
<div id="my-widget" class="my-widget" data-label="{{ data.label }}">…</div>

<script type="module">
    import { MyWidgetController } from '{% static "main.js" %}';
    await MyWidgetController.initializeController('#my-widget');
</script>
```

By convention a controller has a static `initializeController(selector)` that constructs the
controller, sets its `focusElementSelector` to the selector, and passes it to
`App.initializeController({ controller: controller })`. Taking the selector is what lets a widget
shown several times on a page start one controller per root, each root with its own id; nothing
in `App` is kept per class except singletons, so each instance is independent.

`App.initializeController()` always takes a controller the caller has constructed, so the
constructor can take arguments. The selector is set on it first: by the caller, as above, or as a
default on the class (`focusElementSelector = '#tab-page'`) for an element there's only ever one
of. A controller with no element, such as one that only watches the window, leaves it `null`.
`App.initializeController()`:

1. when `focusElementSelector` is set and an element matches it, binds the two: the element's
   `__controller` is the controller, the controller's `__element` is the element, and the
   controller is added to its parent element's `__childControllers`, with `__parentElement`
   pointing back. When no element matches, nothing is bound and a warning names the controller
   and its selector, since a controller with no element silently does nothing;
2. awaits `initState()`;
3. registers the controller as a singleton, when `registerAsSingleton` is true;
4. calls `setState()`;
5. calls `afterFirstSetState()`.

So `initState()` looks elements up and adds listeners, and never calls `setState()` itself,
since `App` calls it next. `dispose()` is there to override, but nothing in the framework calls
it; a project that removes a controller's element calls it.

**State drives the DOM.** A controller keeps state in fields, an event handler only changes them
and calls `setState()`, and `setState()` writes the whole DOM from the fields. A DOM change made
in an event handler is lost or contradicted by the next `setState()`.

**A controller's shape,** as `ww_create_page` and `ww_create_widget` write it:

- **DOM references live on a module-level `class Elements`**, held as
  `private elements = new Elements()`, each field typed `HTMLElement | null = null`, since a lookup
  can find nothing. The controller's own fields are state only, so `this.loading` and
  `this.elements.submitButton` can't be confused.
- **Elements are looked up once, in `buildElements()`**, and read from `this.elements` everywhere
  else. Looking them up inside `this.__element` keeps each instance to its own root.
  `buildElements()` and `initializeListeners()` are `protected`: a subclass may override them, and
  other controllers have no business calling them.
- **Data for one element is a `data-` attribute on the controller's root**, read from
  `this.__element.dataset`, not from child elements, hidden inputs or inline JSON. Data every page
  shares, such as the signed-in user, is on a project-owned state class the document template
  fills, such as the starter site's `AppState`.

**Which element lookup.** `getElementByIdOrWarn()` claims an element is always on the page, and
logs a warning when it isn't. Use `document.getElementById()` for one the template renders only
sometimes, where `null` is expected, so the warning keeps meaning something. `bindClick()` is
deprecated: it looks the element up a second time; bind on the element already found.

## Singletons and readiness

Two controllers on one page talk through the singleton registry. One registers itself with
`registerAsSingleton: true`, and the other fetches it with `App.getSingleton(ChildController)`,
which returns `null` when none is registered.

**The registry is keyed on the class itself, not its name.** Production builds minify class
names (`class u extends c`), so two controllers can share a `constructor.name`. Nothing in the
framework reads `constructor.name` or `Class.name`, and nothing in a project should.

Controllers start concurrently, each from its own `<script>`, and a singleton is only registered
after its `initState()`. So the controller asking for it may run first. The child signals that
it is ready with a `Completer`, a promise resolved from outside:

```typescript
export class ChildController extends Controller {
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

`Controller` only deals with the DOM. Anything a project has an opinion about stays out of it,
so the framework doesn't impose that opinion:

- **No logging.** It calls `console.warn` only for a real problem, such as
  `getElementByIdOrWarn()` finding nothing. A project that wants logging declares a label in each
  class and calls its own logger. `logInfo`/`logWarn`/`logError` helpers on `Controller` were
  tried and removed: they chose the logger for the project, and labelled messages with
  `this.constructor.name`, which a production build minifies to a letter or two.
- **No network method.** A `Controller.fetch()` was tried and moved out, because the HTTP client
  is the project's choice (plain `fetch`, axios, a wrapper of its own).
- **No state.** `App` holds only the framework's mechanics.
- **No CSP nonce.** Whether a site sends a Content Security Policy is its own security decision,
  so nothing the package ships mentions a nonce. A project that uses one adds it to its own
  `<script>` tags.
