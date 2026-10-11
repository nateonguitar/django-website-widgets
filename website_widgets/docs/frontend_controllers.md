# Frontend Controllers

The framework's TypeScript: `Controller`, the base class of every page and widget controller,
`App`, which starts controllers and holds the singleton registry, and `Completer`. Read this
before writing a controller, or when two controllers need to talk to each other.

Primary code, in `ts/website_widgets/` beside `AGENTS.md`:
- `controller.ts` — `Controller`
- `app.ts` — `App`: `initializeController()`, `registerSingleton()`, `getSingleton()`
- `completer.ts` — `Completer`
- `README.md` — the don't-edit notice, the package version and the list of files init wrote

## The files belong to the package

**Never edit the framework's TypeScript files.** They are the package's code, copied into the
project by `python manage.py init_website_widgets` only because a bundler needs them in the
project tree. Rerunning init after a package upgrade overwrites them, so an edit is lost; with
the folder committed, the diff shows what init replaced. A project changes behaviour by
subclassing `Controller` or `App` in its own files. A project's own frontend state, such as the
logged-in user or feature flags, lives in its own classes, never on `App`.

## A controller's lifecycle

A widget's template starts its controller from a `<script type="module">` that imports it from
the bundle:

```django
<script type="module">
    import { MyWidgetController } from '{% static "main.js" %}';
    MyWidgetController.initializeController();
</script>
```

By convention a controller has a static `initializeController()` that calls
`App.initializeController({ controllerClass: MyWidgetController })`, which:

1. constructs the controller, or takes the one passed as `controllerInstance`;
2. when `focusElementSelector` is set and an element matches it, binds the two: the element's
   `__controller` is the controller, the controller's `__element` is the element, and the
   controller is added to its parent element's `__childControllers`, with `__parentElement`
   pointing back. When no element matches, nothing is bound and nothing is logged;
3. awaits `initState()`;
4. registers the controller as a singleton, when `registerAsSingleton` is true;
5. calls `setState()`;
6. calls `afterFirstSetState()`.

So `initState()` looks elements up and adds listeners, and never calls `setState()` itself,
since `App` calls it next. An override calls `super.initState()` first. `dispose()` is there to
override, ending with `super.dispose()`, but nothing in the framework calls it; a project that
removes a controller's element calls it.

**State drives the DOM.** A controller keeps state in fields, an event handler only changes them
and calls `setState()`, and `setState()` writes the whole DOM from the fields. A DOM change made
in an event handler is lost or contradicted by the next `setState()`.

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
        super.afterFirstSetState();
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
