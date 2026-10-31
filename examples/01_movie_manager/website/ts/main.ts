// The bundle's entry point, built to static/main.js and static/bundled-styles.css. Templates
// import what it exports: import { AppState } from '{% static "main.js" %}'.

// Your own styles and exports go here, above the sections the commands manage.
import './styles.scss';
import './web-components/loading-spinner.scss';
import { LoadingSpinner } from './web-components/loading-spinner';

export { App } from './website_widgets/app';
export { Controller } from './website_widgets/controller';
export { Completer } from './website_widgets/completer';
export { AppState } from './app-state';
export { AppUrls } from './app-urls';
export { Cart } from './cart';

// Every page loads this bundle, so it defines the custom elements. An element already on the
// page upgrades when its definition arrives.
customElements.define(LoadingSpinner.htmlTag, LoadingSpinner);

// Managed by ww_create_widget. Do not manually edit this section.
// {{ WIDGET STYLES START }}
import '../widgets/account_menu/account_menu.scss';
import '../widgets/appbar/appbar.scss';
import '../widgets/confirm_dialog/confirm_dialog.scss';
import '../widgets/copy_table/copy_table.scss';
import '../widgets/movie_card/movie_card.scss';
import '../widgets/movie_results/movie_results.scss';
import '../widgets/rental_row/rental_row.scss';
// {{ WIDGET STYLES END }}

// Managed by ww_create_page. Do not manually edit this section.
// {{ PAGE STYLES START }}
import '../pages/add_movie_page/add_movie_page.scss';
import '../pages/cart_page/cart_page.scss';
import '../pages/find_movie_page/find_movie_page.scss';
import '../pages/home_page/home_page.scss';
import '../pages/movie_page/movie_page.scss';
import '../pages/my_history_page/my_history_page.scss';
import '../pages/my_movies_page/my_movies_page.scss';
import '../pages/sign_in_page/sign_in_page.scss';
import '../pages/who_has_what_page/who_has_what_page.scss';
// {{ PAGE STYLES END }}

// Managed by ww_create_widget. Do not manually edit this section.
// {{ WIDGET CONTROLLERS START }}
export { AccountMenuController } from '../widgets/account_menu/account_menu';
export { AppbarController } from '../widgets/appbar/appbar';
export { ConfirmDialogController } from '../widgets/confirm_dialog/confirm_dialog';
export { MovieCardController } from '../widgets/movie_card/movie_card';
export { RatingPickerController } from '../widgets/rating_picker/rating_picker';
export { RentalRowController } from '../widgets/rental_row/rental_row';
// {{ WIDGET CONTROLLERS END }}

// Managed by ww_create_page. Do not manually edit this section.
// {{ PAGE CONTROLLERS START }}
export { AddMoviePageController } from '../pages/add_movie_page/add_movie_page';
export { CartPageController } from '../pages/cart_page/cart_page';
export { FindMoviePageController } from '../pages/find_movie_page/find_movie_page';
export { MyHistoryPageController } from '../pages/my_history_page/my_history_page';
export { SignInPageController } from '../pages/sign_in_page/sign_in_page';
// {{ PAGE CONTROLLERS END }}
