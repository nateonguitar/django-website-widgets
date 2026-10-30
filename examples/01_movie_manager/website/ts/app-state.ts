export class SignedInUser {
    id = 0;
    username = '';
}

/**
 * Data every page shares, set once by document_template.html. Any controller imports it. Data
 * only one element needs goes in data- attributes on that element instead.
 */
export class AppState {
    static siteName = '';
    // Sent as the X-CSRFToken header with every POST.
    static csrfToken = '';
    // null when nobody is signed in.
    static user: SignedInUser | null = null;
}
