import { App } from 'django-website-widgets';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FindMoviePageController } from '../pages/find_movie_page/find_movie_page';
import { AppUrls } from '../ts/app-urls';
import { Fixtures } from './fixtures';

/**
 * The search answers with HTML, so the stub answers with what the endpoint really rendered
 * (`find_movie_page__search_answer.html`) rather than a hand-copied fragment that would drift
 * from the MovieResults template.
 */
describe('FindMoviePageController', () => {
    beforeEach(async () => {
        App.clearSingletons();
        Fixtures.mount('find_movie_page.html');
        AppUrls.endpoint_search_movies = '/api/movies/search';
        const findMoviePageController = new FindMoviePageController();
        await App.initController(findMoviePageController, '#find-movie-page');
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    function search(text: string): void {
        const queryInput = document.querySelector<HTMLInputElement>('.find-movie-page__query')!;
        const submitEvent = new Event('submit', { cancelable: true });
        queryInput.value = text;
        queryInput.form!.dispatchEvent(submitEvent);
    }

    it('shows the endpoint\'s results in place and keeps the URL in step', async () => {
        const answer = Fixtures.read('find_movie_page__search_answer.html');
        const response = new Response(answer, { status: 200 });
        const fetch = vi.fn().mockResolvedValue(response);
        vi.stubGlobal('fetch', fetch);

        search('Paddington');

        await vi.waitFor(() => {
            const titleHeadings = document.querySelectorAll('.find-movie-page__results .movie-card__title');
            const titles = Array.from(
                titleHeadings,
                (titleHeading) => titleHeading.textContent?.trim(),
            );
            expect(titles).toContain('Paddington');
        });
        const [requestedUrl] = fetch.mock.calls[0];
        expect(requestedUrl).toBe('/api/movies/search?q=Paddington');
        expect(window.location.search).toBe('?q=Paddington');
    });

    it('says what went wrong when the server fails', async () => {
        const response = new Response('', { status: 502 });
        const fetch = vi.fn().mockResolvedValue(response);
        vi.stubGlobal('fetch', fetch);
        const errorMessage = document.querySelector<HTMLElement>('.find-movie-page__error');

        search('Paddington');

        await vi.waitFor(() => {
            expect(errorMessage?.hidden).toBe(false);
        });
        expect(errorMessage?.textContent).toContain('502');
    });
});
