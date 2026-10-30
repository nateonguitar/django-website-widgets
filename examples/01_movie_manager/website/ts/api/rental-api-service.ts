import { AppUrls } from "../app-urls";
import { ApiResult, ApiService, MessageErrorResponse } from "./api-service";

/** CheckoutResponseDto. */
export class CheckoutResponse {
    rental_ids: number[] = [];
}

/** CheckoutConflictResponseDto: nothing was recorded, because these ran out. */
export class CheckoutConflictResponse {
    message = '';
    unavailable_movie_ids: number[] = [];
}

/** ReturnRentalResponseDto. */
export class ReturnRentalResponse {
    title = '';
}

export type CheckoutResult =
    | ApiResult<200, CheckoutResponse>
    // An empty cart.
    | ApiResult<400, MessageErrorResponse>
    | ApiResult<409, CheckoutConflictResponse>;

export type ReturnRentalResult =
    | ApiResult<200, ReturnRentalResponse>
    | ApiResult<404, MessageErrorResponse>;

/** The rentals router's endpoints, api/endpoints/rentals/. */
export class RentalApiService extends ApiService {
    private static _instance: RentalApiService | null = null;

    /** The one RentalApiService; see MovieApiService.instance. */
    static get instance(): RentalApiService {
        RentalApiService._instance ??= new RentalApiService();
        return RentalApiService._instance;
    }

    private constructor() {
        super();
    }

    async checkout(movieIds: number[]): Promise<CheckoutResult> {
        return this._post<CheckoutResult>(AppUrls.endpoint_checkout, { movie_ids: movieIds }, [200, 400, 409]);
    }

    async returnRental(rentalId: string): Promise<ReturnRentalResult> {
        // The URL arrives as /api/rentals/{rental_id}/return.
        const url = AppUrls.endpoint_return_rental.replace('{rental_id}', encodeURIComponent(rentalId));
        return this._post<ReturnRentalResult>(url, null, [200, 404]);
    }
}
