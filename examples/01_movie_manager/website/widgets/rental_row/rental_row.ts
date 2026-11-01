import { Controller } from "django-website-widgets";
import { ApiError } from "../../ts/api/api-service";
import { RentalApiService } from "../../ts/api/rental-api-service";

class Elements {
    returnButton: HTMLButtonElement | null = null;
    message: HTMLElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.returnButton = root.querySelector('.rental-row__return');
        this.message = root.querySelector('.rental-row__message');
    }
}

export class RentalRowController extends Controller {
    private elements = new Elements();
    private rentalId = '';
    private returning = false;
    private returned = false;
    private message = '';

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
        this.rentalId = this.rootElement?.dataset.rentalId ?? '';
    }

    public setState(): void {
        const elements = this.elements;
        this.rootElement?.classList.toggle('rental-row--returned', this.returned);
        if (elements.returnButton) {
            elements.returnButton.hidden = this.returned;
            elements.returnButton.disabled = this.returning;
        }
        if (elements.message) {
            elements.message.textContent = this.message;
        }
    }

    protected initializeListeners(): void {
        this.elements.returnButton?.addEventListener('click', () => this.returnMovie());
    }

    private async returnMovie(): Promise<void> {
        this.returning = true;
        this.message = '';
        this.setState();
        try {
            const result = await RentalApiService.instance.returnRental(this.rentalId);
            if (result.status === 200) {
                this.returned = true;
                this.message = 'Returned. Thanks!';
            } else {
                this.message = result.body.message;
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.returning = false;
        this.setState();
    }
}
