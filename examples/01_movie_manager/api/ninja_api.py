from ninja import NinjaAPI

from api.endpoints.auth import auth_router
from api.endpoints.copies import copies_router
from api.endpoints.movies import movies_router
from api.endpoints.rentals import rentals_router

# Imported so each module's decorator adds its endpoint to the router above it.
from api.endpoints.auth import endpoint_sign_in, endpoint_sign_out  # noqa: F401
from api.endpoints.copies import endpoint_report_copy  # noqa: F401
from api.endpoints.movies import endpoint_add_copies, endpoint_create_movie, endpoint_search_movies  # noqa: F401
from api.endpoints.rentals import endpoint_checkout, endpoint_return_rental  # noqa: F401


# Reversed as 'api:<url_name>', such as reverse('api:checkout').
movie_manager_api = NinjaAPI(title='Movie manager', urls_namespace='api')
movie_manager_api.add_router('/auth', auth_router)
movie_manager_api.add_router('/copies', copies_router)
movie_manager_api.add_router('/movies', movies_router)
movie_manager_api.add_router('/rentals', rentals_router)
