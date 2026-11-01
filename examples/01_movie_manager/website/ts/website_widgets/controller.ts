export class Controller {
    /**
     * Set to true on a subclass that other controllers reach through `App.getSingleton()`.
     * `App.initController()` registers it, so a page's template can't forget to.
     */
    static readonly singleton: boolean = false;

    /**
     * The element `App.initController()`'s selector matched, set by `App` before `initState()`
     * runs. Look elements up inside it, `this.rootElement.querySelector('#title')`, so a
     * controller only finds what its own template rendered. Null when `App` was given no
     * selector, or nothing matched it.
     */
    public rootElement: HTMLElement | null = null;

    public async initState(): Promise<void> {
        // To be overridden by subclasses
    }

    public setState(): void {
        // To be overridden by subclasses
    }

    public afterFirstSetState(): void {
        // To be overridden by subclasses
    }
}
