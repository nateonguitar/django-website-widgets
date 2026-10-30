export type ThemeChoice = 'system' | 'light' | 'dark';

/**
 * Light, dark, or whatever the system prefers. The choice is the `data-theme` attribute on
 * <html>, which styles.scss keys its colour variables on, and a cookie, which AppPage reads so
 * the next page arrives already in the theme.
 */
export class Theme {
    // AppPage.THEME_COOKIE reads the same name.
    static cookieName = 'movie_manager_theme';
    // Fired on document when the colours change, by a choice here or by the system's setting.
    static changedEvent = 'theme-changed';

    private static systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)');

    static current(): ThemeChoice {
        return (document.documentElement.dataset.theme as ThemeChoice | undefined) ?? 'system';
    }

    static choose(choice: ThemeChoice): void {
        document.documentElement.dataset.theme = choice;
        // A year, on every path. Not HttpOnly: this script is what writes it.
        document.cookie = `${Theme.cookieName}=${choice}; path=/; max-age=31536000; samesite=lax`;
        document.dispatchEvent(new Event(Theme.changedEvent));
    }

    /**
     * A colour variable's current value, for drawing that can't use var(), such as a chart on a
     * <canvas>.
     */
    static color(variableName: string): string {
        return getComputedStyle(document.documentElement).getPropertyValue(variableName).trim();
    }

    /** Runs the callback whenever the colours change, including the system switching under 'system'. */
    static onChange(callback: () => void): void {
        document.addEventListener(Theme.changedEvent, callback);
        Theme.systemPrefersDark.addEventListener('change', () => {
            if (Theme.current() === 'system') {
                callback();
            }
        });
    }
}
