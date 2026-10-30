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
     * Starts a controller the caller has constructed: binds it to the element matching its
     * `focusElementSelector`, runs `initState()`, optionally registers it as a singleton, then runs
     * `setState()` and `afterFirstSetState()`.
     *
     * The selector is set on the controller before it's passed in, either by the caller (a widget
     * shown several times, each root with its own id) or as a default on the class. A controller
     * with no element, such as one that only watches the window, leaves it `null`.
     *
     * @param options.controller - The controller to start.
     * @param options.registerAsSingleton - Registers the controller for `App.getSingleton()`.
     * @returns The controller, started.
     *
     * ```
     * const controller = new MovieCardController();
     * controller.focusElementSelector = '#movie-card-12';
     * await App.initializeController({ controller: controller });
     * ```
     */
    static async initializeController<T extends Controller>({
        controller,
        registerAsSingleton = false,
    }: {
        controller: T;
        registerAsSingleton?: boolean;
    }): Promise<T> {
        if (controller.focusElementSelector !== null) {
            const element = document.querySelector<HTMLElement>(controller.focusElementSelector);
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
                console.warn(
                    `${controller.constructor.name}: nothing matches its focusElementSelector, `
                    + `${controller.focusElementSelector}`);
            }
        }

        await controller.initState();
        if (registerAsSingleton) {
            App.registerSingleton<T>(controller);
        }
        controller.setState();
        controller.afterFirstSetState();

        return controller;
    }
}
