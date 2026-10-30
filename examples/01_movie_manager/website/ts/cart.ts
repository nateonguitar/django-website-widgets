import { AppState } from "./app-state";

export class CartItem {
    movieId = 0;
    title = '';
}

/**
 * The movies the signed-in user means to take, kept in localStorage so the cart survives a
 * reload and a closed tab (sessionStorage would lose it with the tab). Keyed by the user's id,
 * so two people on one family computer each have their own. Nothing is recorded on the server
 * until checkout.
 */
export class Cart {
    static storageKey(): string | null {
        return AppState.user ? `movie-manager-cart-${AppState.user.id}` : null;
    }

    static items(): CartItem[] {
        const key = Cart.storageKey();
        if (!key) {
            return [];
        }
        try {
            const stored = JSON.parse(localStorage.getItem(key) ?? '[]');
            return Array.isArray(stored) ? stored : [];
        } catch {
            // Hand-edited or from an older version of the site: start again.
            return [];
        }
    }

    static has(movieId: number): boolean {
        return Cart.items().some((item) => item.movieId === movieId);
    }

    static add(item: CartItem): void {
        if (!Cart.has(item.movieId)) {
            Cart.save([...Cart.items(), item]);
        }
    }

    static remove(movieId: number): void {
        Cart.save(Cart.items().filter((item) => item.movieId !== movieId));
    }

    static clear(): void {
        Cart.save([]);
    }

    private static save(items: CartItem[]): void {
        const key = Cart.storageKey();
        if (!key) {
            return;
        }
        localStorage.setItem(key, JSON.stringify(items));
    }
}
