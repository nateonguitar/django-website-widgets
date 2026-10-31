# Frontend Controllers

The framework's TypeScript: `Controller`, the base class of every page and widget controller,
`App`, which starts controllers and holds the singleton registry, and `Completer`. Read this
before writing a controller, or when two controllers need to talk to each other.

Primary code, in the app's `ts/website_widgets/`:
- `controller.ts` — `Controller`
- `app.ts` — `App`: `initController()`, `registerSingleton()`, `getSingleton()`
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

**The template is the one place a selector is chosen,** a few lines from the id it names, so the
two can't drift apart unseen. A widget shown several times on a page passes each root's own id
(`'#my-widget-{{ data.movie.id }}'`) and gets one controller per root; nothing in `App` is kept per
class except singletons, so each instance is independent. A controller with no element, such as
one that only watches the window, is started with no selector, `App.initController(new
ThemeController())`, and gets no DOM binding: `__element` stays `null`, while the lifecycle and
the singleton registry work as for any other. The caller constructs the controller, so its
constructor can take arguments.

`App.initController(controller, selector)`:

1. when a selector is given and an element matches it, binds the two: the element's
   `__controller` is the controller, the controller's `__element` is the element, and the
   controller is added to its parent element's `__childControllers`, with `__parentElement`
   pointing back. When no element matches, nothing is bound and a warning names the controller
   and its selector, since a controller that was meant to have an element silently does nothing
   without one;
2. awaits `initState()`;
3. registers the controller as a singleton, when its class says `static readonly singleton = true`;
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
