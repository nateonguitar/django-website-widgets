import { AppUrls } from "../app-urls";
import { ApiResult, ApiService, FieldErrorsResponse, MessageErrorResponse } from "./api-service";

/** SignInResponseDto. */
export class SignInResponse {
    redirect = '';
}

/** SignOutResponseDto. */
export class SignOutResponse {
    redirect = '';
}

export type SignInResult =
    | ApiResult<200, SignInResponse>
    | ApiResult<400, FieldErrorsResponse>
    // A wrong password, or (403) a page whose CSRF token is out of date.
    | ApiResult<401 | 403, MessageErrorResponse>;

export type SignOutResult = ApiResult<200, SignOutResponse>;

/** The auth router's endpoints, api/endpoints/auth/. */
export class AuthApiService extends ApiService {
    private static _instance: AuthApiService | null = null;

    /** The one AuthApiService; see MovieApiService.instance. */
    static get instance(): AuthApiService {
        AuthApiService._instance ??= new AuthApiService();
        return AuthApiService._instance;
    }

    private constructor() {
        super();
    }

    async signIn(username: string, password: string, next: string): Promise<SignInResult> {
        const payload = { username: username, password: password, next: next };
        return this._post<SignInResult>(AppUrls.endpoint_sign_in, payload, [200, 400, 401, 403]);
    }

    async signOut(): Promise<SignOutResult> {
        return this._post<SignOutResult>(AppUrls.endpoint_sign_out, null, [200]);
    }
}
