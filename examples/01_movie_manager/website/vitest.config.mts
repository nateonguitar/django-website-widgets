import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        // A fake DOM in Node, so a controller finds its elements with no browser and no build.
        environment: 'happy-dom',
        environmentOptions: {
            happyDOM: {
                settings: {
                    // A fixture's <script>s import the built main.js; here the test mounts each
                    // controller itself, so no script runs and nothing is fetched for one.
                    disableJavaScriptEvaluation: true,
                    disableJavaScriptFileLoading: true,
                    // The stylesheet <link> too; nothing here measures layout.
                    disableCSSFileLoading: true,
                    handleDisabledFileLoadingAsSuccess: true,
                },
            },
        },
        // Renders the HTML fixtures with Python first, so each run tests the current templates.
        globalSetup: ['./tests/vitest.global-setup.ts'],
    },
});
