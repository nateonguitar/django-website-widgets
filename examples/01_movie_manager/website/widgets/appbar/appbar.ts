import { App, Completer, Controller } from "django-website-widgets";
import { Cart } from "../../ts/cart";

class Elements {
    cartCount: HTMLElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.cartCount = root.querySelector('.appbar__cart-count');
    }
}

/**
 * A singleton: a controller that changes the cart tells the appbar through
 * `App.getSingleton(AppbarController)`. Controllers start concurrently, each from its own
 * <script>, so one may ask before the appbar has registered; it awaits
 * `singletonInitializationCompleter` first. The account menu inside it is a widget with its
 * own controller, AccountMenuController.
 */
export class AppbarController extends Controller {
    // App.initController() registers it, for App.getSingleton().
    static readonly singleton = true;
    public static singletonInitializationCompleter = new Completer<null>();

    private elements = new Elements();
    private cartCount = 0;

    /** Waits for the appbar to be registered, then hands it over. */
    public static async instance(): Promise<AppbarController | null> {
        await AppbarController.singletonInitializationCompleter.promise;
        return App.getSingleton(AppbarController);
    }

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
        this.cartCount = Cart.items().length;
    }

    public afterFirstSetState(): void {
        AppbarController.singletonInitializationCompleter.resolve(null);
    }

    /** Another controller on this page changed the cart. */
    public cartChanged(): void {
        this.cartCount = Cart.items().length;
        this.setState();
    }

    public setState(): void {
        if (this.elements.cartCount) {
            this.elements.cartCount.textContent = String(this.cartCount);
        }
    }

    protected initializeListeners(): void {
        // Another tab changed the cart. The browser fires this only in the other tabs, never in
        // the one that wrote to localStorage.
        window.addEventListener('storage', (event) => {
            if (event.key === Cart.storageKey()) {
                this.cartChanged();
            }
        });
    }
}
