import { describe, expect, it, vi } from 'vitest';

// Imported, not mocked: the class reads window.matchMedia when it's defined, which happy-dom has.
import { Theme } from './theme';

describe('Theme', () => {
    it('follows the system until a theme is chosen', () => {
        delete document.documentElement.dataset.theme;

        expect(Theme.current()).toBe('system');
    });

    it('writes the choice on <html> and in the cookie, and announces it', () => {
        const changed = vi.fn();
        document.addEventListener(Theme.changedEvent, changed);

        Theme.choose('dark');

        const theme = document.documentElement.dataset.theme;
        const expectedCookie = `${Theme.cookieName}=dark`;
        expect(theme).toBe('dark');
        expect(document.cookie).toContain(expectedCookie);
        expect(changed).toHaveBeenCalledOnce();
    });
});
