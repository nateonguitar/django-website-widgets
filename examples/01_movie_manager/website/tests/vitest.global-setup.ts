import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

/**
 * Runs once before every Vitest run: the Python tests tagged `vitest_fixtures` render the HTML
 * the JS tests load (`tests/test_vitest_fixtures.py`). Under `vitest --watch` it doesn't run
 * again, so a template edit needs Vitest restarted to reach its fixture.
 *
 * `PYTHON` is how this project runs manage.py, `poetry run python` unless set; a project in a
 * container sets its own.
 */
export default function setup(): void {
    const projectRoot = fileURLToPath(new URL('../..', import.meta.url));
    const python = process.env.PYTHON ?? 'poetry run python';
    execSync(`${python} manage.py test --tag=vitest_fixtures`, { cwd: projectRoot, stdio: 'inherit' });
}
