import { App } from 'django-website-widgets';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Fixtures } from '../../tests/fixtures';
import { ConfirmDialogController } from './confirm_dialog';

describe('ConfirmDialogController', () => {
    beforeEach(() => {
        App.clearSingletons();
        // Any document from AppWidgetTestCase holds the confirm dialog's <template>, as every page does.
        Fixtures.mount('movie_card__signed_in.html');
    });

    async function openedConfirmDialog(): Promise<HTMLDialogElement> {
        return vi.waitFor(() => {
            const confirmDialog = document.querySelector<HTMLDialogElement>('dialog.confirm-dialog');
            expect(confirmDialog?.open).toBe(true);
            return confirmDialog!;
        });
    }

    it('answers true when yes is clicked', async () => {
        const answer = ConfirmDialogController.show({ message: 'Take the rest?', yesLabel: 'Take the rest' });
        const confirmDialog = await openedConfirmDialog();
        const confirmMessage = confirmDialog.querySelector('.confirm-dialog__message');
        const yesButton = confirmDialog.querySelector<HTMLButtonElement>('.confirm-dialog__yes')!;
        expect(confirmMessage?.textContent).toBe('Take the rest?');

        yesButton.click();

        await expect(answer).resolves.toBe(true);
        const confirmDialogAfter = document.querySelector('dialog.confirm-dialog');
        expect(confirmDialogAfter).toBeNull();
    });

    it('answers null when closed without a choice', async () => {
        const answer = ConfirmDialogController.show({ message: 'Take the rest?' });
        const confirmDialog = await openedConfirmDialog();

        // What Escape does: closes the dialog with no button clicked.
        confirmDialog.close();

        await expect(answer).resolves.toBeNull();
    });
});
