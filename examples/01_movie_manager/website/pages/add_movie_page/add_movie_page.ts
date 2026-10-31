import { Controller } from "../../ts/website_widgets/controller";
import { ApiError } from "../../ts/api/api-service";
import { CreateMovieRequest, MovieApiService } from "../../ts/api/movie-api-service";
import { MovieCardController, MovieChosenDetail } from "../../widgets/movie_card/movie_card";

type Kind = 'new' | 'copy';

class Elements {
    kindInputs: HTMLInputElement[] = [];
    newForm: HTMLFormElement | null = null;
    fieldErrors: HTMLElement[] = [];
    copySection: HTMLElement | null = null;
    search: HTMLInputElement | null = null;
    searchResults: HTMLElement | null = null;
    copiesForm: HTMLFormElement | null = null;
    chosenTitle: HTMLElement | null = null;
    copies: HTMLInputElement | null = null;
    message: HTMLElement | null = null;
    added: HTMLElement | null = null;
    spinner: HTMLElement | null = null;
}

/** The new-movie form's messages from a 400, keyed by field. */
class NewMovieErrors {
    title = '';
    year = '';
    genre = '';
    rating = '';
    copies = '';
}

export class AddMoviePageController extends Controller {
    private static typingPauseMs = 250;

    private elements = new Elements();
    private kind: Kind = 'new';
    private saving = false;
    private newMovieErrors = new NewMovieErrors();
    private message = '';
    // What was just added, shown until the next save.
    private added = '';
    private chosen: MovieChosenDetail | null = null;
    private typingTimer: number | undefined;
    private searchInFlight: AbortController | null = null;

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
    }

    protected buildElements(): void {
        const root = this.__element;
        const elements = this.elements;
        elements.kindInputs = Array.from(root?.querySelectorAll<HTMLInputElement>('input[name="kind"]') ?? []);
        elements.newForm = root?.querySelector<HTMLFormElement>('.add-movie-page__new') ?? null;
        elements.fieldErrors = Array.from(root?.querySelectorAll<HTMLElement>('.add-movie-page__field-error') ?? []);
        elements.copySection = root?.querySelector<HTMLElement>('.add-movie-page__copy') ?? null;
        elements.search = root?.querySelector<HTMLInputElement>('.add-movie-page__search') ?? null;
        elements.searchResults = root?.querySelector<HTMLElement>('.add-movie-page__search-results') ?? null;
        elements.copiesForm = root?.querySelector<HTMLFormElement>('.add-movie-page__copies-form') ?? null;
        elements.chosenTitle = root?.querySelector<HTMLElement>('.add-movie-page__chosen-title') ?? null;
        elements.copies = root?.querySelector<HTMLInputElement>('.add-movie-page__copies') ?? null;
        elements.message = root?.querySelector<HTMLElement>('.add-movie-page__message') ?? null;
        elements.added = root?.querySelector<HTMLElement>('.add-movie-page__added') ?? null;
        elements.spinner = root?.querySelector<HTMLElement>('.add-movie-page__spinner') ?? null;
    }

    public setState(): void {
        const elements = this.elements;
        if (elements.newForm) {
            elements.newForm.hidden = this.kind !== 'new';
        }
        if (elements.copySection) {
            elements.copySection.hidden = this.kind !== 'copy';
        }
        for (const fieldError of elements.fieldErrors) {
            const field = fieldError.dataset.field as keyof NewMovieErrors;
            fieldError.textContent = this.newMovieErrors[field] ?? '';
        }
        if (elements.copiesForm) {
            elements.copiesForm.hidden = this.chosen === null;
        }
        if (elements.chosenTitle) {
            elements.chosenTitle.textContent = this.chosen?.title ?? '';
        }
        for (const button of this.__element?.querySelectorAll<HTMLButtonElement>('form button[type="submit"]') ?? []) {
            button.disabled = this.saving;
        }
        if (elements.message) {
            elements.message.hidden = !this.message;
            elements.message.textContent = this.message;
        }
        if (elements.added) {
            elements.added.hidden = !this.added;
            elements.added.textContent = this.added;
        }
        if (elements.spinner) {
            elements.spinner.hidden = !this.saving;
        }
    }

    protected initializeListeners(): void {
        const elements = this.elements;
        for (const input of elements.kindInputs) {
            input.addEventListener('change', () => {
                this.kind = input.value as Kind;
                this.message = '';
                this.setState();
            });
        }
        elements.newForm?.addEventListener('submit', (event) => {
            event.preventDefault();
            this.createMovie();
        });
        elements.search?.addEventListener('input', () => {
            window.clearTimeout(this.typingTimer);
            this.typingTimer = window.setTimeout(() => this.search(), AddMoviePageController.typingPauseMs);
        });
        // The cards don't know this page; a chosen one says so with an event that bubbles up here.
        elements.searchResults?.addEventListener(MovieCardController.movieChosenEvent, (event) => {
            this.chosen = (event as CustomEvent<MovieChosenDetail>).detail;
            this.message = '';
            this.setState();
        });
        elements.copiesForm?.addEventListener('submit', (event) => {
            event.preventDefault();
            this.addCopies();
        });
    }

    private async search(): Promise<void> {
        const query = this.elements.search?.value.trim() ?? '';
        this.searchInFlight?.abort();
        const inFlight = new AbortController();
        this.searchInFlight = inFlight;
        const params = new URLSearchParams({ purpose: 'choose' });
        if (query) {
            params.set('q', query);
        }
        try {
            const html = await MovieApiService.instance.searchHtml(params, inFlight.signal);
            // A fragment, not innerHTML, so each card's <script> runs and starts its controller.
            const fragment = document.createRange().createContextualFragment(html);
            this.elements.searchResults?.replaceChildren(fragment);
        } catch {
            // Aborted by a newer search, or offline: the next keystroke searches again.
        }
    }

    private async createMovie(): Promise<void> {
        const form = this.elements.newForm;
        if (!form) {
            return;
        }
        const values = new FormData(form);
        const year = Number.parseInt(String(values.get('year')), 10);
        const copies = Number.parseInt(String(values.get('copies')), 10);
        const request = new CreateMovieRequest();
        request.title = String(values.get('title') ?? '');
        request.year = Number.isNaN(year) ? null : year;
        request.genre = String(values.get('genre') ?? '');
        request.rating = String(values.get('rating') ?? '');
        request.copies = Number.isNaN(copies) ? 0 : copies;

        this.startSaving();
        try {
            const result = await MovieApiService.instance.createMovie(request);
            if (result.status === 201) {
                this.added = `Added ${result.body.title}.`;
                form.reset();
            } else {
                this.newMovieErrors = Object.assign(new NewMovieErrors(), result.body.errors);
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.saving = false;
        this.setState();
    }

    private async addCopies(): Promise<void> {
        if (!this.chosen) {
            return;
        }
        const typedCopies = Number.parseInt(this.elements.copies?.value ?? '', 10);
        // A blank box is sent as 0, so the endpoint's message says what's allowed.
        const copies = Number.isNaN(typedCopies) ? 0 : typedCopies;

        this.startSaving();
        try {
            const result = await MovieApiService.instance.addCopies(this.chosen.movieId, copies);
            if (result.status === 201) {
                this.added = `${result.body.title} now has ${result.body.total_copies} copies.`;
                this.chosen = null;
                this.elements.searchResults?.replaceChildren();
                if (this.elements.search) {
                    this.elements.search.value = '';
                }
            } else if (result.status === 400) {
                this.message = result.body.errors.copies ?? '';
            } else {
                this.message = result.body.message;
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.saving = false;
        this.setState();
    }

    /** Disables the forms and clears what the last save said. */
    private startSaving(): void {
        this.saving = true;
        this.newMovieErrors = new NewMovieErrors();
        this.message = '';
        this.added = '';
        this.setState();
    }
}
