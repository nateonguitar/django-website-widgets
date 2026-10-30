import { App } from "../../ts/website_widgets/app";
import { Completer } from "../../ts/website_widgets/completer";
import { Controller } from "../../ts/website_widgets/controller";

class Elements {
    dialog: HTMLDialogElement | null = null;
    message: HTMLElement | null = null;
    yesButton: HTMLButtonElement | null = null;
    noButton: HTMLButtonElement | null = null;
}

/**
 * Asks a yes-or-no question and answers with the click:
 * `const yes = await ConfirmDialogController.ask({ message: 'Take the rest?' })`.
 *
 * Each ask() clones the <template> the ConfirmDialog widget renders into a <dialog> of its own,
 * with its own controller and its own Completer. Questions asked back to back, or one opened
 * over another, so each resolve only their own caller's promise. The answer comes from a click
 * that happens later, which a plain await has nothing to wait on; the Completer is the promise
 * ask() hands back now and the dialog resolves then.
 */
export class ConfirmDialogController extends Controller {
    // Numbers each dialog's id, so a selector finds exactly one.
    private static asked = 0;

    private elements = new Elements();
    private answer = new Completer<boolean>();

    // App takes a controller already constructed, so one can take what it shows as arguments.
    constructor(
        private message: string,
        private yesLabel: string,
        private noLabel: string,
    ) {
        super();
    }

    public static async ask({
        message,
        yesLabel = 'Yes',
        noLabel = 'No',
    }: {
        message: string;
        yesLabel?: string;
        noLabel?: string;
    }): Promise<boolean> {
        const template = document.querySelector<HTMLTemplateElement>('#confirm-dialog-template');
        const dialog = template?.content.querySelector<HTMLDialogElement>('dialog')?.cloneNode(true) as HTMLDialogElement | undefined;
        if (!dialog) {
            throw new Error('No #confirm-dialog-template on this page. The document template renders it.');
        }
        ConfirmDialogController.asked += 1;
        dialog.id = `confirm-dialog-${ConfirmDialogController.asked}`;
        document.body.append(dialog);

        const controller = new ConfirmDialogController(message, yesLabel, noLabel);
        controller.focusElementSelector = `#${dialog.id}`;
        await App.initializeController({ controller: controller });
        return controller.answer.promise;
    }

    public async initState(): Promise<void> {
        this.buildElements();
        this.initializeListeners();
        // A screen reader announces the question as the dialog's name. The id is per clone,
        // so it can't be written into the template.
        const elements = this.elements;
        if (elements.dialog && elements.message) {
            elements.message.id = `${elements.dialog.id}__message`;
            elements.dialog.setAttribute('aria-labelledby', elements.message.id);
        }
    }

    protected buildElements(): void {
        const root = this.__element;
        const elements = this.elements;
        elements.dialog = root as HTMLDialogElement | null;
        elements.message = root?.querySelector<HTMLElement>('.confirm-dialog__message') ?? null;
        elements.yesButton = root?.querySelector<HTMLButtonElement>('.confirm-dialog__yes') ?? null;
        elements.noButton = root?.querySelector<HTMLButtonElement>('.confirm-dialog__no') ?? null;
    }

    public setState(): void {
        const elements = this.elements;
        if (elements.message) {
            elements.message.textContent = this.message;
        }
        if (elements.yesButton) {
            elements.yesButton.textContent = this.yesLabel;
        }
        if (elements.noButton) {
            elements.noButton.textContent = this.noLabel;
        }
    }

    public afterFirstSetState(): void {
        // Over anything already open, another question included: the browser stacks modal
        // dialogs, and only the top one takes clicks and Escape.
        this.elements.dialog?.showModal();
    }

    protected initializeListeners(): void {
        const dialog = this.elements.dialog;
        // Every way it closes ends here: a button, whose value the form leaves in returnValue,
        // or Escape, which leaves it empty and so answers no.
        dialog?.addEventListener('close', () => {
            this.answer.resolve(dialog.returnValue === 'yes');
            dialog.remove();
        });
    }
}
