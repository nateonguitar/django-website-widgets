import { AppUrls } from "../app-urls";
import { ApiResult, ApiService, FieldErrorsResponse, MessageErrorResponse } from "./api-service";

/** CreateMovieRequestDto. */
export class CreateMovieRequest {
    title = '';
    year: number | null = null;
    genre = '';
    rating = '';
    copies = 1;
}

/** CreateMovieResponseDto. */
export class CreateMovieResponse {
    movie_id = 0;
    title = '';
}

/** AddCopiesResponseDto. */
export class AddCopiesResponse {
    title = '';
    total_copies = 0;
}

export type CreateMovieResult =
    | ApiResult<201, CreateMovieResponse>
    | ApiResult<400, FieldErrorsResponse>;

export type AddCopiesResult =
    | ApiResult<201, AddCopiesResponse>
    | ApiResult<400, FieldErrorsResponse>
    | ApiResult<404, MessageErrorResponse>;

/** The movies router's endpoints, api/endpoints/movies/. */
export class MovieApiService extends ApiService {
    private static _instance: MovieApiService | null = null;

    /**
     * The one MovieApiService, made the first time it's asked for. A service keeps nothing per
     * caller, so every controller shares it. Constructing it has nothing to wait on, unlike a
     * singleton controller, so no Completer is needed.
     */
    static get instance(): MovieApiService {
        MovieApiService._instance ??= new MovieApiService();
        return MovieApiService._instance;
    }

    // Private, so `MovieApiService.instance` is the only way to get one.
    private constructor() {
        super();
    }

    /** The MovieResults widget's HTML, for the search in `params`. */
    async searchHtml(params: URLSearchParams, signal: AbortSignal): Promise<string> {
        return this._getHtml(AppUrls.endpoint_search_movies, params, signal);
    }

    async createMovie(request: CreateMovieRequest): Promise<CreateMovieResult> {
        return this._post<CreateMovieResult>(AppUrls.endpoint_create_movie, request, [201, 400]);
    }

    async addCopies(movieId: number, copies: number): Promise<AddCopiesResult> {
        // The URL arrives as /api/movies/{movie_id}/copies.
        const url = AppUrls.endpoint_add_copies.replace('{movie_id}', String(movieId));
        return this._post<AddCopiesResult>(url, { copies: copies }, [201, 400, 404]);
    }
}
