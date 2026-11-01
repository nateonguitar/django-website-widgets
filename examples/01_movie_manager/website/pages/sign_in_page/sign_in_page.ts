import { Controller } from "../../ts/website_widgets/controller";
import { ApiError } from "../../ts/api/api-service";
import { AuthApiService } from "../../ts/api/auth-api-service";

class Elements {
    form: HTMLFormElement | null = null;
    username: HTMLInputElement | null = null;
    password: HTMLInputElement | null = null;
    submitButton: HTMLButtonElement | null = null;
    spinner: HTMLElement | null = null;
    message: HTMLElement | null = null;
    fieldErrors: HTMLElement[] = [];

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.form = root.querySelector('.sign-in-page__form');
        this.username = root.querySelector('.sign-in-page__username');
        this.password = root.querySelector('.sign-in-page__password');
        this.submitButton = root.querySelector('.sign-in-page__submit-button');
        this.spinner = root.querySelector('.sign-in-page__spinner');
        this.message = root.querySelector('.sign-in-page__message');
        this.fieldErrors = Array.from(root.querySelectorAll('.sign-in-page__field-error'));
    }
}

/** Each field's message from a 400, keyed by the field's name. */
class FieldErrors {
    username = '';
    password = '';
}

export class SignInPageController extends Controller {
    private elements = new Elements();
    private next = '';
    private submitting = false;
    private fieldErrors = new FieldErrors();
    // Anything that isn't one field's fault: wrong password, a server error, no connection.
    private message = '';

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
        this.next = this.rootElement?.dataset.next ?? '';
    }

    public afterFirstSetState(): void {
        this.elements.username?.focus();
    }

    public setState(): void {
        const elements = this.elements;
        // Disabled while the request runs, so a double click doesn't sign in twice.
        if (elements.submitButton) {
            elements.submitButton.disabled = this.submitting;
        }
        if (elements.spinner) {
            elements.spinner.hidden = !this.submitting;
        }
        for (const fieldError of elements.fieldErrors) {
            const field = fieldError.dataset.field as keyof FieldErrors;
            fieldError.textContent = this.fieldErrors[field] ?? '';
        }
        if (elements.message) {
            elements.message.hidden = !this.message;
            elements.message.textContent = this.message;
        }
    }

    protected initializeListeners(): void {
        this.elements.form?.addEventListener('submit', (event) => {
            event.preventDefault();
            this.signIn();
        });
    }

    private async signIn(): Promise<void> {
        this.submitting = true;
        this.fieldErrors = new FieldErrors();
        this.message = '';
        this.setState();
        try {
            const username = this.elements.username?.value ?? '';
            const password = this.elements.password?.value ?? '';
            const result = await AuthApiService.instance.signIn(username, password, this.next);
            if (result.status === 200) {
                // Stays disabled: the page is leaving.
                window.location.href = result.body.redirect;
                return;
            }
            if (result.status === 400) {
                this.fieldErrors = Object.assign(new FieldErrors(), result.body.errors);
            } else {
                this.message = result.body.message;
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.submitting = false;
        this.setState();
    }
}
