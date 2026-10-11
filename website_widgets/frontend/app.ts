import { Controller } from "./controller";

export class App {
    // Keyed on the class itself: production builds minify class names, so two
    // controllers can share a `constructor.name`.
    private static singletons = new Map<Function, unknown>();

    static registerSingleton<T>(instance: T): void {
        App.singletons.set((instance as any).constructor, instance);
    }

    static getSingleton<T>(classType: new () => T): T | null {
        const instance = App.singletons.get(classType);
        return (instance as T) ?? null;
    }

    /**
     * Creates a controller (or takes `controllerInstance`), binds it to the element matching its
     * `focusElementSelector`, runs `initState()`, optionally registers it as a singleton, then runs
     * `setState()` and `afterFirstSetState()`.
     *
     * @param options.controllerClass - The controller class, instantiated when no instance is given.
     * @param options.controllerInstance - An already-constructed controller to initialize instead.
     * @param options.registerAsSingleton - Registers the controller for `App.getSingleton()`.
     * @returns The initialized controller.
     *
     * ```
     * import { App, ForgotPasswordPageController } from '{% static "main.js" %}';
     * await App.initializeController({
     *     controllerClass: ForgotPasswordPageController,
     * });
     * ```
     */
    static async initializeController<T extends Controller>({
        controllerInstance,
        controllerClass,
        registerAsSingleton = false,
    }: {
        controllerInstance?: T,
        controllerClass: new () => T;
        registerAsSingleton?: boolean;
    }): Promise<T> {
        const controller = controllerInstance || new controllerClass();

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
