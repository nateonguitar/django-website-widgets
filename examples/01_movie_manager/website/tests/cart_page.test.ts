import { App, Completer } from 'django-website-widgets';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CartPageController } from '../pages/cart_page/cart_page';
import { AppState } from '../ts/app-state';
import { AppUrls } from '../ts/app-urls';
import { Cart } from '../ts/cart';
import { AppbarController } from '../widgets/appbar/appbar';
import { Fixtures } from './fixtures';

/**
 * The cart page against a stubbed server. JSON bodies are written here, small and shaped like
 * the endpoint's schemas; the endpoint's own tests in api/tests/ hold it to them.
 */
describe('CartPageController', () => {
    beforeEach(async () => {
        App.clearSingletons();
        AppbarController.singletonInitializationCompleter = new Completer<null>();
        localStorage.clear();
        Fixtures.mount('cart_page.html');
        AppState.user = { id: 1, username: 'alex' };
        AppState.csrfToken = 'test-csrf-token';
        AppUrls.endpoint_checkout = '/api/rentals/checkout';
        Cart.add({ movieId: 5, title: 'Paddington' });
        Cart.add({ movieId: 6, title: 'Paddington 2' });
        const appbarController = new AppbarController();
        const cartPageController = new CartPageController();
        await App.initController(appbarController, '#appbar');
        await App.initController(cartPageController, '#cart-page');
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    function answerWith(...bodies: [number, object][]) {
        const fetch = vi.fn();
        for (const [status, body] of bodies) {
            const json = JSON.stringify(body);
            const response = new Response(json, { status: status });
            fetch.mockResolvedValueOnce(response);
        }
        // The global, so whatever the page sends requests through is covered.
        vi.stubGlobal('fetch', fetch);
        return fetch;
    }

    function clickCheckout(): void {
        const checkoutButton = document.querySelector<HTMLButtonElement>('.cart-page__checkout-button')!;
        checkoutButton.click();
    }

    it('empties the cart and says so when checkout succeeds', async () => {
        const fetch = answerWith([200, { rental_ids: [11, 12] }]);
        const doneMessage = document.querySelector<HTMLElement>('.cart-page__done');

        clickCheckout();

        await vi.waitFor(() => {
            expect(doneMessage?.hidden).toBe(false);
        });
        const [url, request] = fetch.mock.calls[0];
        const sent = JSON.parse(request.body);
        const csrfToken = request.headers['X-CSRFToken'];
        const itemsLeft = Cart.items();
        expect(url).toBe('/api/rentals/checkout');
        expect(sent).toEqual({ movie_ids: [5, 6] });
        expect(csrfToken).toBe('test-csrf-token');
        expect(itemsLeft).toEqual([]);
    });

    it('offers the rest and checks out again when a movie ran out', async () => {
        const fetch = answerWith(
            [409, { message: 'Paddington ran out.', unavailable_movie_ids: [5] }],
            [200, { rental_ids: [12] }],
        );

        clickCheckout();

        const confirmDialog = await vi.waitFor(() => {
            const openedConfirmDialog = document.querySelector<HTMLDialogElement>('dialog.confirm-dialog');
            expect(openedConfirmDialog?.open).toBe(true);
            return openedConfirmDialog!;
        });
        const confirmMessage = confirmDialog.querySelector('.confirm-dialog__message');
        const yesButton = confirmDialog.querySelector<HTMLButtonElement>('.confirm-dialog__yes')!;
        expect(confirmMessage?.textContent).toContain('Paddington ran out');
        yesButton.click();

        await vi.waitFor(() => {
            expect(fetch).toHaveBeenCalledTimes(2);
        });
        const [, secondRequest] = fetch.mock.calls[1];
        const sentAgain = JSON.parse(secondRequest.body);
        expect(sentAgain).toEqual({ movie_ids: [6] });
    });
});
