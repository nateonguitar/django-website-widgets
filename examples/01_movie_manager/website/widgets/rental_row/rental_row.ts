import { Controller } from "../../ts/website_widgets/controller";
import { ApiError } from "../../ts/api/api-service";
import { RentalApiService } from "../../ts/api/rental-api-service";

class Elements {
    returnButton: HTMLButtonElement | null = null;
    message: HTMLElement | null = null;
}

export class RentalRowController extends Controller {
    private elements = new Elements();
    private rentalId = '';
    private returning = false;
    private returned = false;
    private message = '';

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        this.rentalId = this.__element?.dataset.rentalId ?? '';
    }

    protected buildElements(): void {
        this.elements.returnButton = this.__element?.querySelector<HTMLButtonElement>('.rental-row__return') ?? null;
        this.elements.message = this.__element?.querySelector<HTMLElement>('.rental-row__message') ?? null;
    }

    public setState(): void {
        const elements = this.elements;
        this.__element?.classList.toggle('rental-row--returned', this.returned);
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
