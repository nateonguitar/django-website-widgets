import { App, Completer } from 'django-website-widgets';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Fixtures } from '../../tests/fixtures';
import { AppState } from '../../ts/app-state';
import { Cart } from '../../ts/cart';
import { AppbarController } from '../appbar/appbar';
import { MovieCardController } from './movie_card';

describe('MovieCardController', () => {
    beforeEach(async () => {
        // Vitest keeps one copy of each module for every test in this file, so static state
        // carries over: the package's singleton registry, and the appbar's readiness signal.
        App.clearSingletons();
        AppbarController.singletonInitializationCompleter = new Completer<null>();
        localStorage.clear();
        Fixtures.mount('movie_card__signed_in.html');
        // Set by the fixture's AppState <script>, which doesn't run here. Cart keys on the id.
        AppState.user = { id: 1, username: 'alex' };
        const appbarController = new AppbarController();
        await App.initController(appbarController, '#appbar');
    });

    async function mountMovieCard(): Promise<HTMLElement> {
        const movieCard = document.querySelector<HTMLElement>('.movie-card')!;
        const movieCardController = new MovieCardController();
        const selector = `.movie-card[data-key="${movieCard.dataset.key}"]`;
        await App.initController(movieCardController, selector);
        return movieCard;
    }

    it('offers to add the movie when it is not in the cart', async () => {
        const movieCard = await mountMovieCard();

        const cartButton = movieCard.querySelector('.movie-card__action');
        expect(cartButton?.textContent).toBe('Add to cart');
    });

    it('puts the movie in the cart and tells the appbar when clicked', async () => {
        const movieCard = await mountMovieCard();
        const cartButton = movieCard.querySelector<HTMLButtonElement>('.movie-card__action')!;
        const cartCountBadge = document.querySelector('.appbar__cart-count');

        cartButton.click();

        await vi.waitFor(() => {
            expect(cartCountBadge?.textContent).toBe('1');
        });
        const movieId = Number(movieCard.dataset.movieId);
        const inCart = Cart.has(movieId);
        expect(cartButton.textContent).toBe('Remove from cart');
        expect(inCart).toBe(true);
    });
});
