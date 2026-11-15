import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/** The HTML `test_vitest_fixtures.py` wrote, by file name, for a Vitest test to mount controllers on. */
export class Fixtures {
    // The folder VitestFixturesTestCase.FIXTURES_DIR writes to. A path, not a URL: under
    // happy-dom the global URL is the fake DOM's, which Node's file functions refuse.
    private static folder = join(dirname(fileURLToPath(import.meta.url)), '..', 'vitest_fixtures');

    static read(name: string): string {
        return readFileSync(join(Fixtures.folder, name), 'utf-8');
    }

    /**
     * Puts the fixture's body into the test's document. Through innerHTML, so the <html>, <head>
     * and <body> wrappers go and no <script> runs: the test starts each controller itself.
     */
    static mount(name: string): void {
        document.body.innerHTML = Fixtures.read(name);
    }
}
