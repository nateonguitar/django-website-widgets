import { DialogController } from "../../ts/dialog-controller";

class Elements {
    message: HTMLElement | null = null;
    yesButton: HTMLButtonElement | null = null;
    noButton: HTMLButtonElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.message = root.querySelector('.confirm-dialog__message');
        this.yesButton = root.querySelector('.confirm-dialog__yes');
        this.noButton = root.querySelector('.confirm-dialog__no');
    }
}

/**
 * Asks a yes-or-no question and answers with the click, or null when dismissed without one:
 * `const takeTheRest = await ConfirmDialogController.show({ message: 'Take the rest?' })`.
 *
 * DialogController.openFrame() clones the DialogFrame named confirm-dialog, with this widget's content
 * inside, into a <dialog> of its own for each question, so questions never share an element or an
 * answer.
 */
export class ConfirmDialogController extends DialogController<boolean | null> {
    private elements = new Elements();
    // Left null when Escape or the backdrop closes it: no answer was given, which isn't a no.
    private chosen: boolean | null = null;

    // App takes a controller already constructed, so one can take what it shows as arguments.
    constructor(
        private message: string,
        private yesLabel: string,
        private noLabel: string,
    ) {
        super();
    }

    public static show({
        message,
        yesLabel = 'Yes',
        noLabel = 'No',
    }: {
        message: string;
        yesLabel?: string;
        noLabel?: string;
    }): Promise<boolean | null> {
        const controller = new ConfirmDialogController(message, yesLabel, noLabel);
        return DialogController.openFrame('confirm-dialog', controller);
    }

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
    }

    protected initializeListeners(): void {
        this.elements.yesButton?.addEventListener('click', () => this.choose(true));
        this.elements.noButton?.addEventListener('click', () => this.choose(false));
    }

    // Closing resolves the caller's promise with answer(), so the choice is stored first.
    private choose(chosen: boolean): void {
        this.chosen = chosen;
        this.dialog?.close();
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

    protected answer(): boolean | null {
        return this.chosen;
    }
}
