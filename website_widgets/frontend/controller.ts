export class Controller {
    public __element: HTMLElement | null = null;
    public __parentElement: HTMLElement | null = null;

    /** Set this if a dom element is associated with this controller */
    public focusElementSelector: string | null = null;

    /** Call super.initState() as the first line of sub-class initState() */
    public async initState(): Promise<void> {
        // To be overridden by subclasses
    }

    public setState(): void {
        // To be overridden by subclasses
    }

    public afterFirstSetState(): void {
        // To be overridden by subclasses
    }

    /** Call super.dispose() as the final line of sub-class dispose() */
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

    /**
     * @deprecated Look the element up once into the controller's elements and bind on it,
     * `this.elements.saveButton?.addEventListener('click', handler)`. This looks the element
     * up a second time, and warns for an element the template renders conditionally.
     */
    bindClick({ elementId, handler }: { elementId: string; handler: EventListener }): void {
        const element = this.getElementByIdOrWarn(elementId);
        if (element) {
            element.addEventListener("click", handler);
        }
    }
}
