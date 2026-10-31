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
        # parameters as placeholders such as {rental_id} for the frontend to fill, and a static
        # file, when the frontend needs one, from django.templatetags.static.static(). That's the
        # URL a versioning static storage (ManifestStaticFilesStorage) changes when the file is
        # rebuilt; a hand-written '/static/...' path never changes, so browsers keep their stale
        # copy.
        self.context.data['urls'] = {
            # The Django Ninja endpoints, reversed by their url_name like any Django route.
            'endpoint_sign_in': reverse_template('api:sign_in'),
            'endpoint_sign_out': reverse_template('api:sign_out'),
            'endpoint_search_movies': reverse_template('api:search_movies'),
            'endpoint_create_movie': reverse_template('api:create_movie'),
            'endpoint_add_copies': reverse_template('api:add_copies'),
            'endpoint_checkout': reverse_template('api:checkout'),
            'endpoint_return_rental': reverse_template('api:return_rental'),
        }
