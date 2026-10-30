/**
 * The URLs the frontend can't build itself, filled in by the AppUrls widget
 * (widgets/app_urls/) before any controller runs. A route's parameters stay as
 * placeholders, such as `{rental_id}`, for the controller to fill.
 */
export class AppUrls {
    static static_bundled_styles: string;
    static endpoint_sign_in: string;
    static endpoint_sign_out: string;
    static endpoint_search_movies: string;
    static endpoint_create_movie: string;
    static endpoint_add_copies: string;
    static endpoint_checkout: string;
    static endpoint_return_rental: string;
}
