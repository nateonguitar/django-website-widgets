import { App } from "./website_widgets/app";
import { Completer } from "./website_widgets/completer";
import { Controller } from "./website_widgets/controller";

/**
 * The base of a dialog its caller awaits:
 * `const takeTheRest = await ConfirmDialogController.show({...})`.
 *
 * It is one half of a pair. `DialogFrame` (the Python widget) renders the <dialog>, inside a
 * <template>, around a dialog's own content widget. A subclass's static show() constructs a
 * controller with what it shows and hands it to openFrame() with the frame's `name`. openFrame()
 * clones the frame's <dialog>, starts the controller on the clone, and returns a promise of the
 * subclass's answer(). Every call gets its own element, controller and Completer, so dialogs
 * shown back to back, or one opened over another, each resolve only their own caller's promise.
 *
 * The answer comes from a click that happens later, which a plain await has nothing to wait on;
 * the Completer is the promise openFrame() hands back now and the dialog's close event resolves
 * then.
 *
 * openFrame() does all of the base's work, so a subclass writes initState(), setState() and its
 * listeners like any other controller, with no super call to forget.
 */
export abstract class DialogController<R> extends Controller {
    // Numbers each clone's id, so its selector finds exactly one element.
    private static opened = 0;

    /**
     * Whether a click on the backdrop closes the dialog, answering as a dismissal. The dialog
     * decides, never its caller: a form a stray click would wipe sets this to false.
     */
    protected closesOnBackdropClick = true;

    private readonly answered = new Completer<R>();

    // The clone openFrame() made, which is also this controller's root.
    private dialogElement: HTMLDialogElement | null = null;

    protected get dialog(): HTMLDialogElement | null {
        return this.dialogElement;
    }

    /**
     * What the caller's promise resolves with, read once the dialog has closed, however it
     * closed. Whatever produces the result (a button's choice, a saved form) stores it in a field
     * and then calls `dialog.close()`; this returns that field, still at its starting value when
     * Escape, the backdrop or the frame's close button closed the dialog.
     */
    protected abstract answer(): R;

    /** Opens the <dialog> the DialogFrame named `name` renders, run by `controller`. */
    protected static async openFrame<R>(name: string, controller: DialogController<R>): Promise<R> {
        const dialog = DialogController.cloneFrame(name);
        DialogController.opened += 1;
        dialog.id = `dialog-${DialogController.opened}`;
        DialogController.labelDialog(dialog);
        document.body.append(dialog);

        controller.dialogElement = dialog;
        DialogController.listenForClose(dialog, controller);
        await App.initController(controller, `#${dialog.id}`);
        // Over anything already open, another question included: the browser stacks modal
        // dialogs, and only the top one takes clicks and Escape.
        dialog.showModal();
        return controller.answered.promise;
    }

    private static cloneFrame(name: string): HTMLDialogElement {
        const template = document.querySelector<HTMLTemplateElement>(`#${name}-template`);
        const source = template?.content.querySelector('dialog');
        if (!source) {
            throw new Error(`This page renders no DialogFrame named ${name}, so its dialog can't open.`);
        }
        return source.cloneNode(true) as HTMLDialogElement;
    }

    // A screen reader announces the element marked data-dialog-label (the frame's title, or the
    // content's own) as the dialog's name. The id is per clone, so it can't be in the template.
    private static labelDialog(dialog: HTMLDialogElement): void {
        const label = dialog.querySelector('[data-dialog-label]');
        if (!label) return;
        label.id = `${dialog.id}__label`;
        dialog.setAttribute('aria-labelledby', label.id);
    }

    private static listenForClose<R>(
        dialog: HTMLDialogElement,
        controller: DialogController<R>,
    ): void {
        const closeButton = dialog.querySelector('.dialog-frame__close');
        closeButton?.addEventListener('click', () => dialog.close());
        dialog.addEventListener('click', (event) => {
            if (controller.closesOnBackdropClick && DialogController.landedOnBackdrop(dialog, event)) {
                dialog.close();
            }
        });
        // Every way it closes ends here, so the promise resolves in one place: a button that
        // stored its result and called close(), Escape, the backdrop, or the frame's close button.
        dialog.addEventListener('close', () => {
            controller.answered.resolve(controller.answer());
            dialog.remove();
        });
    }

    // A click on the backdrop targets the <dialog> itself, but so does one on its padding, so
    // the click's position decides.
    private static landedOnBackdrop(dialog: HTMLDialogElement, event: MouseEvent): boolean {
        if (event.target !== dialog) return false;
        const box = dialog.getBoundingClientRect();
        const inside = event.clientX >= box.left
            && event.clientX <= box.right
            && event.clientY >= box.top
            && event.clientY <= box.bottom;
        return !inside;
    }
}
