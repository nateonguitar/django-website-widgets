import { Controller } from "./controller";

export class App {
    // Keyed on the class itself: production builds minify class names, so two
    // controllers can share a `constructor.name`.
    private static singletons = new Map<Function, unknown>();

    static registerSingleton<T>(instance: T): void {
        App.singletons.set((instance as any).constructor, instance);
    }

    // Any constructor, so a controller whose constructor takes arguments can still be looked up.
    static getSingleton<T>(classType: abstract new (...args: any[]) => T): T | null {
        const instance = App.singletons.get(classType);
        return (instance as T) ?? null;
    }

    /**
     * Starts a controller: binds it to the element `selector` matches, runs `initState()`,
     * registers it when its class says `static readonly singleton = true`, then runs `setState()`
     * and `afterFirstSetState()`.
     *
     * Called from the `<script>` in the template that renders the controller's root, so the
     * selector sits beside the id it names. A widget shown several times passes each root's own
     * id. A controller with no element, such as one that only watches the window, passes none and
     * gets no DOM binding; it still gets the lifecycle and, when its class says so, the singleton
     * registry.
     *
     * ```
     * <script type="module">
     *     import { App, MovieCardController } from '{% static "main.js" %}';
     *     await App.initController(new MovieCardController(), '#movie-card-12');
     * </script>
     * ```
     *
     * @returns The controller, started.
     */
    static async initController<T extends Controller>(controller: T, selector: string | null = null): Promise<T> {
        if (selector !== null) {
            const element = document.querySelector<HTMLElement>(selector);
            if (element) {
                (element as any).__controller = controller;
                controller.__element = element;
                if (element.parentElement) {
                    const parentElement: any = element.parentElement;
                    controller.__parentElement = parentElement;
                    if (parentElement.__childControllers === undefined) {
                        parentElement.__childControllers = [];
                    }
                    parentElement.__childControllers.push(controller);
                }
            } else {
                // Otherwise the controller runs with no element, every lookup inside it finds
                // nothing, and the page just doesn't respond. Usually the template's root id and
                // the selector have drifted apart.
                console.warn(`${controller.constructor.name}: nothing matches the selector ${selector}`);
            }
        }

        await controller.initState();
        if ((controller.constructor as typeof Controller).singleton) {
            App.registerSingleton<T>(controller);
        }
        controller.setState();
        controller.afterFirstSetState();

        return controller;
    }
}
