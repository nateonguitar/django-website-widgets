# One file per model's admin. Django's autodiscovery imports only api.admin, so each is
# imported here for its @admin.register to run.
from api.admin import copy_admin, movie_admin, rental_admin, user_admin  # noqa: F401
