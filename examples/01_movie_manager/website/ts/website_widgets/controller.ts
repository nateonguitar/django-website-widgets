export class Controller {
    /**
     * Set to true on a subclass that other controllers reach through `App.getSingleton()`.
     * `App.initController()` registers it, so a page's template can't forget to.
     */
    static readonly singleton: boolean = false;

    /** The element `App.initController()`'s selector matched, or null when it was given none. */
    public __element: HTMLElement | null = null;
    public __parentElement: HTMLElement | null = null;

    public async initState(): Promise<void> {
        // To be overridden by subclasses
    }

    public setState(): void {
        // To be overridden by subclasses
    }

    public afterFirstSetState(): void {
        // To be overridden by subclasses
    }

    public dispose(): void {
        // To be overridden by subclasses
    }

    /**
     * Use this when the element is always present on load, so a warning appears if an
     * element that should be there isn't found. Use document.getElementById when a null
     * is sometimes intended, such as an element the template only renders conditionally.
     */
    getElementByIdOrWarn<T extends HTMLElement>(elementId: string): T | null {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Could not find element with ID: ${elementId}`);
            return null;
        }
        return element as T;
    }
}
