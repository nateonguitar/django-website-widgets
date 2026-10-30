import { App } from "../../ts/website_widgets/app";
import { Controller } from "../../ts/website_widgets/controller";
import { Cart } from "../../ts/cart";
import { AppbarController } from "../appbar/appbar";

class Elements {
    actionButton: HTMLButtonElement | null = null;
}

export class MovieChosenDetail {
    movieId = 0;
    title = '';
}

/**
 * One instance per card. A 'choose' card doesn't know which page it's on: it dispatches a
 * bubbling `movie-chosen` event from its root, and whichever page holds it listens.
 */
export class MovieCardController extends Controller {
    public static movieChosenEvent = 'movie-chosen';

    private elements = new Elements();
    private movieId = 0;
    private title = '';
    private available = 0;
    private purpose = 'cart';
    private inCart = false;

    public static async initializeController(selector: string): Promise<void> {
        const controller = new MovieCardController();
        controller.focusElementSelector = selector;
        await App.initializeController({ controller: controller });
    }

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        const dataset = this.__element?.dataset;
        this.movieId = Number(dataset?.movieId);
        this.title = dataset?.title ?? '';
        this.available = Number(dataset?.available);
        this.purpose = dataset?.purpose ?? 'cart';
        this.inCart = Cart.has(this.movieId);
    }

    protected buildElements(): void {
        this.elements.actionButton = this.__element?.querySelector<HTMLButtonElement>('.movie-card__action') ?? null;
    }

    public setState(): void {
        const button = this.elements.actionButton;
        if (!button) {
            return;
        }
        if (this.purpose === 'choose') {
            button.textContent = 'Choose';
            button.disabled = false;
        } else if (this.inCart) {
            button.textContent = 'Remove from cart';
            button.disabled = false;
        } else if (this.available > 0) {
            button.textContent = 'Add to cart';
            button.disabled = false;
        } else {
            button.textContent = 'None available';
            button.disabled = true;
        }
    }

    protected initializeListeners(): void {
        this.elements.actionButton?.addEventListener('click', () => this.act());
    }

    private async act(): Promise<void> {
        if (this.purpose === 'choose') {
            const detail: MovieChosenDetail = { movieId: this.movieId, title: this.title };
            this.__element?.dispatchEvent(new CustomEvent(MovieCardController.movieChosenEvent, {
                bubbles: true,
                detail: detail,
            }));
            return;
        }
        if (this.inCart) {
            Cart.remove(this.movieId);
        } else {
            Cart.add({ movieId: this.movieId, title: this.title });
        }
        this.inCart = Cart.has(this.movieId);
        this.setState();
        const appbar = await AppbarController.instance();
        appbar?.cartChanged();
    }
}
