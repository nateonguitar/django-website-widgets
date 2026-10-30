import { AppState } from "../app-state";

/**
 * One answer an endpoint declares in its Ninja `response={...}`: a status and the schema that
 * comes with it. A service method returns a union of these, so checking `result.status === 201`
 * narrows `result.body` to that status's schema.
 */
export interface ApiResult<Status extends number, Body> {
    status: Status;
    body: Body;
}

/** MessageErrorResponseDto: a refusal, worded for the person, shown as it is. */
export class MessageErrorResponse {
    message = '';
}

/** FieldErrorsResponseDto: a form's mistakes, a message for each field. */
export class FieldErrorsResponse {
    errors: Record<string, string> = {};
}

/**
 * A request that got none of the answers its endpoint declares: the server couldn't be reached
 * (status 0), or it answered with a status the endpoint doesn't list, such as Ninja's own 401
 * for an expired session or a proxy's 502.
 */
export class ApiError extends Error {
    readonly status: number;

    constructor(status: number) {
        super(status === 0 ? 'The server could not be reached' : `The server answered ${status}`);
        this.status = status;
    }

    /** A message for the person, for whatever a request threw. */
    static messageFor(error: unknown): string {
        if (error instanceof ApiError && error.status === 0) {
            return "Couldn't reach the server. Check your connection and try again.";
        }
        if (error instanceof ApiError) {
            return `Something went wrong (the server answered ${error.status}). Try again.`;
        }
        return 'Something went wrong. Try again.';
    }
}

/**
 * The base of each endpoint group's service: how a request is sent, kept here so a controller
 * only says what it wants. A subclass has a method per endpoint, named for what it does, whose
 * return type lists the answers the endpoint declares.
 */
export abstract class ApiService {
    /**
     * POSTs `payload` as JSON. Resolves with any of `expectedStatuses`, the ones the endpoint's
     * `response={...}` declares, and throws an ApiError for anything else.
     */
    protected async _post<Result extends ApiResult<number, unknown>>(
        url: string,
        payload: object | null,
        expectedStatuses: Result['status'][],
    ): Promise<Result> {
        const headers: Record<string, string> = {
            // From AppState, which the page filled, not read from the cookie:
            // settings.CSRF_COOKIE_HTTPONLY keeps the cookie out of JavaScript's reach.
            'X-CSRFToken': AppState.csrfToken,
        };
        if (payload !== null) {
            headers['Content-Type'] = 'application/json';
        }
        let response: Response;
        try {
            response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: payload === null ? null : JSON.stringify(payload),
            });
        } catch {
            throw new ApiError(0);
        }
        if (!expectedStatuses.includes(response.status)) {
            throw new ApiError(response.status);
        }
        const body = await response.json();
        return { status: response.status, body: body } as Result;
    }

    /**
     * GETs HTML, such as a widget an endpoint rendered with arender(). An aborted request
     * rejects with the browser's AbortError, so a caller can tell it from a failure.
     */
    protected async _getHtml(url: string, params: URLSearchParams, signal: AbortSignal): Promise<string> {
        let response: Response;
        try {
            response = await fetch(`${url}?${params}`, { signal: signal });
        } catch (error) {
            if (signal.aborted) {
                throw error;
            }
            throw new ApiError(0);
        }
        if (!response.ok) {
            throw new ApiError(response.status);
        }
        return response.text();
    }
}
