import { App } from "../../ts/website_widgets/app";
import { Controller } from "../../ts/website_widgets/controller";
import { AuthApiService } from "../../ts/api/auth-api-service";
import { Cart } from "../../ts/cart";
import { Theme, ThemeChoice } from "../../ts/theme";

class Elements {
    button: HTMLButtonElement | null = null;
    dialog: HTMLDialogElement | null = null;
    themeInputs: HTMLInputElement[] = [];
    signOutButton: HTMLButtonElement | null = null;
    closeButton: HTMLButtonElement | null = null;
}

/**
 * Its own controller inside the appbar's: the appbar keeps the cart count, this keeps the
 * theme and signing out, and neither reaches into the other's elements.
 */
export class AccountMenuController extends Controller {
    private elements = new Elements();
    private theme: ThemeChoice = 'system';
    private signingOut = false;

    public static async initializeController(selector: string): Promise<void> {
        const controller = new AccountMenuController();
        controller.focusElementSelector = selector;
        await App.initializeController({ controller: controller });
    }

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        this.theme = Theme.current();
    }

    protected buildElements(): void {
        const root = this.__element;
        const elements = this.elements;
        elements.button = root?.querySelector<HTMLButtonElement>('.account-menu__button') ?? null;
        elements.dialog = root?.querySelector<HTMLDialogElement>('.account-menu__dialog') ?? null;
        elements.themeInputs = Array.from(root?.querySelectorAll<HTMLInputElement>('.account-menu__theme input') ?? []);
        elements.signOutButton = root?.querySelector<HTMLButtonElement>('.account-menu__sign-out') ?? null;
        elements.closeButton = root?.querySelector<HTMLButtonElement>('.account-menu__close') ?? null;
    }

    public setState(): void {
        const elements = this.elements;
        for (const input of elements.themeInputs) {
            input.checked = input.value === this.theme;
        }
        if (elements.signOutButton) {
            elements.signOutButton.disabled = this.signingOut;
        }
    }

    protected initializeListeners(): void {
        const elements = this.elements;
        elements.button?.addEventListener('click', () => elements.dialog?.showModal());
        elements.closeButton?.addEventListener('click', () => elements.dialog?.close());
        // A click on the backdrop lands on the <dialog> itself; one inside lands on its content.
        elements.dialog?.addEventListener('click', (event) => {
            if (event.target === elements.dialog) {
                elements.dialog.close();
            }
        });
        for (const input of elements.themeInputs) {
            input.addEventListener('change', () => {
                this.theme = input.value as ThemeChoice;
                Theme.choose(this.theme);
                this.setState();
            });
        }
        elements.signOutButton?.addEventListener('click', () => this.signOut());
    }

    private async signOut(): Promise<void> {
        this.signingOut = true;
        this.setState();
        try {
            const result = await AuthApiService.instance.signOut();
            // Cleared only once signed out, so a failed sign-out keeps the cart.
            Cart.clear();
            window.location.href = result.body.redirect;
            return;
        } catch {
            // The button is enabled again to retry.
        }
        this.signingOut = false;
        this.setState();
    }
}
