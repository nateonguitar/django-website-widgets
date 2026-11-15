import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        // A fake DOM in Node, so a controller finds its elements with no browser.
        environment: 'happy-dom',
        include: ['tests/**/*.test.ts'],
    },
});
