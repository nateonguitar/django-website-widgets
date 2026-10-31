import { Controller } from "../../ts/website_widgets/controller";

class Elements {
    select: HTMLSelectElement | null = null;
    description: HTMLElement | null = null;
}

/**
 * Shows what the chosen rating means. Runs on the site and in the Django admin alike: it reads
 * nothing from AppUrls or AppState, which only the site's document template fills.
 */
export class RatingPickerController extends Controller {
    private elements = new Elements();
    // Each rating's description, by value, from the options' data- attributes.
    private descriptions = new Map<string, string>();
    private rating = '';

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        const options = Array.from(this.elements.select?.options ?? []);
        this.descriptions = new Map(options.map((option) => [option.value, option.dataset.description ?? '']));
        this.rating = this.elements.select?.value ?? '';
    }

    protected buildElements(): void {
        const root = this.__element;
        const elements = this.elements;
        elements.select = root?.querySelector<HTMLSelectElement>('.rating-picker__select') ?? null;
        elements.description = root?.querySelector<HTMLElement>('.rating-picker__description') ?? null;
    }

    public setState(): void {
        if (this.elements.description) {
            this.elements.description.textContent = this.descriptions.get(this.rating) ?? '';
        }
    }

    protected initializeListeners(): void {
        const select = this.elements.select;
        select?.addEventListener('change', () => {
            this.rating = select.value;
            this.setState();
        });
        // A form reset changes the choice without a change event. The event fires before the
        // fields are reset, so the choice is read once they have been.
        select?.form?.addEventListener('reset', () => {
            setTimeout(() => {
                this.rating = select.value;
                this.setState();
            });
        });
    }
}
