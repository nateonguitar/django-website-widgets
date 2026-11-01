import { Controller } from "../../ts/website_widgets/controller";
import { ApiError } from "../../ts/api/api-service";
import { MovieApiService } from "../../ts/api/movie-api-service";

class Elements {
    form: HTMLFormElement | null = null;
    query: HTMLInputElement | null = null;
    genre: HTMLSelectElement | null = null;
    rating: HTMLSelectElement | null = null;
    loading: HTMLElement | null = null;
    error: HTMLElement | null = null;
    results: HTMLElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.form = root.querySelector('.find-movie-page__filters');
        this.query = root.querySelector('.find-movie-page__query');
        this.genre = root.querySelector('.find-movie-page__genre');
        this.rating = root.querySelector('.find-movie-page__rating');
        this.loading = root.querySelector('.find-movie-page__loading');
        this.error = root.querySelector('.find-movie-page__error');
        this.results = root.querySelector('.find-movie-page__results');
    }
}

/**
 * Searches as the visitor types or picks, without reloading the page, and keeps the URL's
 * query string in step, so the address bar is always a link to what's on screen.
 */
export class FindMoviePageController extends Controller {
    // Typing waits this long after the last key before searching, rather than once per key.
    private static typingPauseMs = 250;

    private elements = new Elements();
    private loading = false;
    private error = '';
    private typingTimer: number | undefined;
    // Aborted when a newer search starts, so a slow answer can't replace a newer one.
    private inFlight: AbortController | null = null;

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
    }

    public setState(): void {
        const elements = this.elements;
        // The spinner takes the results' place, so the old answer isn't mistaken for the new one.
        if (elements.loading) {
            elements.loading.hidden = !this.loading;
        }
        if (elements.results) {
            elements.results.hidden = this.loading;
        }
        if (elements.error) {
            elements.error.hidden = !this.error;
            elements.error.textContent = this.error;
        }
    }

    protected initializeListeners(): void {
        const elements = this.elements;
        elements.query?.addEventListener('input', () => {
            window.clearTimeout(this.typingTimer);
            this.typingTimer = window.setTimeout(() => this.search(), FindMoviePageController.typingPauseMs);
        });
        elements.genre?.addEventListener('change', () => this.search());
        elements.rating?.addEventListener('change', () => this.search());
        // The form works on its own as a GET to this page; with the controller running, the
        // search happens in place instead of reloading.
        elements.form?.addEventListener('submit', (event) => {
            event.preventDefault();
            this.search();
        });
    }

    /** The form's fields as a query string, leaving out what's blank ("Any"). */
    private searchParams(): URLSearchParams {
        const params = new URLSearchParams();
        const query = this.elements.query?.value.trim() ?? '';
        if (query) {
            params.set('q', query);
        }
        if (this.elements.genre?.value) {
            params.set('genre', this.elements.genre.value);
        }
        if (this.elements.rating?.value) {
            params.set('rating', this.elements.rating.value);
        }
        return params;
    }

    private async search(): Promise<void> {
        const params = this.searchParams();
        // replaceState, not pushState: typing would otherwise leave a history entry per search,
        // and Back would step through them one by one.
        const pageUrl = params.size > 0 ? `${window.location.pathname}?${params}` : window.location.pathname;
        window.history.replaceState(null, '', pageUrl);

        this.inFlight?.abort();
        const inFlight = new AbortController();
        this.inFlight = inFlight;
        this.loading = true;
        this.error = '';
        this.setState();
        try {
            // The endpoint takes the same query string as the page.
            const html = await MovieApiService.instance.searchHtml(params, inFlight.signal);
            this.showResults(html);
        } catch (error) {
            if (inFlight.signal.aborted) {
                // A newer search replaced this one; it shows its own answer.
                return;
            }
            this.error = ApiError.messageFor(error);
        }
        this.loading = false;
        this.setState();
    }

    private showResults(html: string): void {
        const results = this.elements.results;
        if (!results) {
            return;
        }
        // Not innerHTML: a <script> set through innerHTML never runs, and each card starts its
        // own controller from its <script>. A fragment made by the document's range does run
        // them when it's inserted.
        const fragment = document.createRange().createContextualFragment(html);
        results.replaceChildren(fragment);
    }
}
