from django.templatetags.static import static

from website_widgets import Widget, reverse_template


class AppUrls(Widget):
    """
    Hands the frontend its URLs. The template assigns each one to the TypeScript `AppUrls` in
    `ts/app-urls.ts`, so a controller reads `AppUrls.endpoint_checkout` rather than writing a
    path. A new URL is a line here and its declaration there.
    """

    def set_context(self):
        # Only URLs the frontend can't build itself, so they come from the Python side, never a
        # hand-built path: pages and endpoints from reverse_template(), which leaves a route's
        # parameters as placeholders such as {rental_id} for the frontend to fill, and static files
        # from static().
        self.context.data['urls'] = {
            # Web components import the bundled stylesheet into their shadow roots. It must be
            # static()'s URL, the same one the document's <link> uses: a versioning static
            # storage (ManifestStaticFilesStorage) gives a rebuilt stylesheet a new URL there,
            # while a hand-written '/static/bundled-styles.css' never changes and browsers keep
            # serving their stale copy.
            'static_bundled_styles': static('bundled-styles.css'),
            # The Django Ninja endpoints, reversed by their url_name like any Django route.
            'endpoint_sign_in': reverse_template('api:sign_in'),
            'endpoint_sign_out': reverse_template('api:sign_out'),
            'endpoint_search_movies': reverse_template('api:search_movies'),
            'endpoint_create_movie': reverse_template('api:create_movie'),
            'endpoint_add_copies': reverse_template('api:add_copies'),
            'endpoint_checkout': reverse_template('api:checkout'),
            'endpoint_return_rental': reverse_template('api:return_rental'),
        }
