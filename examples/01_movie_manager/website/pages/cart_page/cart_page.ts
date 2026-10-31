import { Controller } from "../../ts/website_widgets/controller";
import { ApiError } from "../../ts/api/api-service";
import { RentalApiService } from "../../ts/api/rental-api-service";
import { Cart, CartItem } from "../../ts/cart";
import { AppbarController } from "../../widgets/appbar/appbar";
import { ConfirmDialogController } from "../../widgets/confirm_dialog/confirm_dialog";

class Elements {
    empty: HTMLElement | null = null;
    items: HTMLUListElement | null = null;
    checkout: HTMLElement | null = null;
    checkoutButton: HTMLButtonElement | null = null;
    spinner: HTMLElement | null = null;
    message: HTMLElement | null = null;
    done: HTMLElement | null = null;
}

export class CartPageController extends Controller {
    private elements = new Elements();
    private items: CartItem[] = [];
    private checkingOut = false;
    private message = '';
    private done = false;
    // Movies the server said ran out, from a 409, marked until they're removed.
    private unavailableMovieIds = new Set<number>();

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        this.items = Cart.items();
    }

    protected buildElements(): void {
        const root = this.__element;
        const elements = this.elements;
        elements.empty = root?.querySelector<HTMLElement>('.cart-page__empty') ?? null;
        elements.items = root?.querySelector<HTMLUListElement>('.cart-page__items') ?? null;
        elements.checkout = root?.querySelector<HTMLElement>('.cart-page__checkout') ?? null;
        elements.checkoutButton = root?.querySelector<HTMLButtonElement>('.cart-page__checkout-button') ?? null;
        elements.spinner = root?.querySelector<HTMLElement>('.cart-page__spinner') ?? null;
        elements.message = root?.querySelector<HTMLElement>('.cart-page__message') ?? null;
        elements.done = root?.querySelector<HTMLElement>('.cart-page__done') ?? null;
    }

    public setState(): void {
        const elements = this.elements;
        const hasItems = this.items.length > 0;
        if (elements.empty) {
            elements.empty.hidden = hasItems || this.done;
        }
        if (elements.items) {
            elements.items.replaceChildren(...this.items.map((item) => this.buildItem(item)));
        }
        if (elements.checkout) {
            elements.checkout.hidden = !hasItems;
        }
        if (elements.checkoutButton) {
            elements.checkoutButton.disabled = this.checkingOut || this.unavailableMovieIds.size > 0;
        }
        if (elements.spinner) {
            elements.spinner.hidden = !this.checkingOut;
        }
        if (elements.message) {
            elements.message.hidden = !this.message;
            elements.message.textContent = this.message;
        }
        if (elements.done) {
            elements.done.hidden = !this.done;
        }
    }

    protected initializeListeners(): void {
        this.elements.checkoutButton?.addEventListener('click', () => this.checkout());
        // The cart changed in another tab.
        window.addEventListener('storage', (event) => {
            if (event.key === Cart.storageKey()) {
                this.items = Cart.items();
                this.setState();
            }
        });
    }

    /** Built here rather than rendered by the server, which never sees what's in the cart. */
    private buildItem(item: CartItem): HTMLLIElement {
        const row = document.createElement('li');
        row.className = 'cart-page__item';
        const title = document.createElement('span');
        title.textContent = item.title;
        row.append(title);
        if (this.unavailableMovieIds.has(item.movieId)) {
            row.classList.add('cart-page__item--unavailable');
            const note = document.createElement('span');
            note.className = 'cart-page__unavailable';
            note.textContent = 'None left';
            row.append(note);
        }
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'text-button';
        remove.textContent = 'Remove';
        remove.disabled = this.checkingOut;
        remove.addEventListener('click', () => this.remove(item.movieId));
        row.append(remove);
        return row;
    }

    private async remove(movieId: number): Promise<void> {
        Cart.remove(movieId);
        this.items = Cart.items();
        this.unavailableMovieIds.delete(movieId);
        if (this.unavailableMovieIds.size === 0) {
            this.message = '';
        }
        this.setState();
        const appbar = await AppbarController.instance();
        appbar?.cartChanged();
    }

    private async checkout(): Promise<void> {
        this.checkingOut = true;
        this.message = '';
        this.setState();
        try {
            const movieIds = this.items.map((item) => item.movieId);
            const result = await RentalApiService.instance.checkout(movieIds);
            if (result.status === 200) {
                Cart.clear();
                this.items = [];
                this.done = true;
                const appbar = await AppbarController.instance();
                appbar?.cartChanged();
            } else if (result.status === 409) {
                // Nothing was recorded. The ones that ran out are marked, and the rest offered.
                this.unavailableMovieIds = new Set(result.body.unavailable_movie_ids);
                this.message = result.body.message;
            } else {
                this.message = result.body.message;
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.checkingOut = false;
        this.setState();
        if (this.unavailableMovieIds.size > 0) {
            await this.offerTheRest();
        }
    }

    /**
     * After a 409, asks whether to take what's left. Yes removes the movies that ran out and
     * checks out again; no leaves them marked, for the person to remove or wait on.
     */
    private async offerTheRest(): Promise<void> {
        const ranOut = this.items.filter((item) => this.unavailableMovieIds.has(item.movieId));
        if (ranOut.length === this.items.length) {
            // Nothing is left to take.
            return;
        }
        const titles = ranOut.map((item) => item.title).join(', ');
        const takeTheRest = await ConfirmDialogController.ask({
            message: `${titles} ran out. Take the rest of your cart?`,
            yesLabel: 'Take the rest',
            noLabel: 'Not now',
        });
        if (!takeTheRest) {
            return;
        }
        for (const item of ranOut) {
            Cart.remove(item.movieId);
        }
        this.items = Cart.items();
        this.unavailableMovieIds.clear();
        this.message = '';
        this.setState();
        const appbar = await AppbarController.instance();
        appbar?.cartChanged();
        await this.checkout();
    }
}
