import { App } from "./app.js";
import { Completer } from "./completer.js";
import { Controller } from "./controller.js";

/**
 * The base of a dialog its caller awaits, like Flutter's `showDialog`:
 * `const takeTheRest = await ConfirmDialogController.show({...})`.
 *
 * A dialog's widget renders its content inside a `<template>`, placed on any page that can show
 * it, with no `<dialog>` and no `<script>`:
 *
 * ```html
 * <template id="confirm-dialog-template" data-dialog-class="confirm-dialog">
 *     <p data-dialog-label>…</p>
 *     <button class="confirm-dialog__yes">Yes</button>
 * </template>
 * ```
 *
 * A subclass's static `show()` constructs a controller with what it shows and hands it to
 * `openDialog()` with that template's selector. `openDialog()` creates a bare `<dialog>`, clones
 * the template's content into it, starts the controller on it, opens it, and returns a promise
 * of the subclass's `answer()`. Every call gets its own element, controller and `Completer`, so
 * dialogs shown back to back, or one over another, each answer only their own caller.
 *
 * Whatever produces the result, a button's choice or a saved form, stores it in a field and then
 * calls `this.dialog.close()`; the one `close` listener resolves the caller's promise with
 * `answer()`, so a dismissal (Escape, the backdrop, a `[data-dialog-close]` button) leaves that
 * field at its starting value, `null` by convention.
 *
 * The template's attributes the dialog reads:
 * - `data-dialog-class` on the `<template>`: classes for the `<dialog>`, for the dialog's styles.
 * - `data-dialog-label` on an element inside: the dialog's accessible name.
 * - `data-dialog-close` on a button inside: closes the dialog with no answer.
 *
 * `openDialog()` does all of the base's work, so a subclass writes `initState()`, `setState()`
 * and its listeners like any other controller, with no `super` call to forget.
 */
export abstract class DialogController<R> extends Controller {
    // Numbers each dialog's id, so its selector finds exactly one element.
    private static opened = 0;

    /**
     * Whether a click on the backdrop closes the dialog with no answer. The dialog decides,
     * never its caller: a form that a stray click would wipe sets this to false.
     */
    protected closesOnBackdropClick = true;

    /**
     * While true, Escape, the backdrop and `[data-dialog-close]` leave the dialog open, so a save
     * in flight isn't dropped. A dialog that sends a request sets it around the request.
     */
    protected saving = false;

    private readonly answered = new Completer<R>();

    // The dialog openDialog() created, which is also this controller's root.
    private dialogElement: HTMLDialogElement | null = null;

    protected get dialog(): HTMLDialogElement | null {
        return this.dialogElement;
    }

    /** What the caller's promise resolves with, read once the dialog has closed, however it closed. */
    protected abstract answer(): R;

    /**
     * Opens a dialog holding a copy of the content of the `<template>` that `templateSelector`
     * matches, run by `controller`, and resolves with its `answer()` once it closes.
     */
    protected static async openDialog<R>(
        controller: DialogController<R>,
        templateSelector: string,
    ): Promise<R> {
        const template = document.querySelector<HTMLTemplateElement>(templateSelector);
        if (!(template instanceof HTMLTemplateElement)) {
            throw new Error(`No <template> on this page matches ${templateSelector}, so its dialog can't open.`);
        }
        const dialog = document.createElement("dialog");
        DialogController.opened += 1;
        dialog.id = `dialog-${DialogController.opened}`;
        const classes = template.dataset.dialogClass?.split(/\s+/).filter(Boolean) ?? [];
        dialog.classList.add(...classes);
        dialog.append(template.content.cloneNode(true));
        DialogController.label(dialog);
        document.body.append(dialog);

        controller.dialogElement = dialog;
        DialogController.listenForClose(dialog, controller);
        await App.initController(controller, `#${dialog.id}`);
        // Over anything already open: the browser stacks modal dialogs, and only the top one
        // takes clicks and Escape.
        dialog.showModal();
        return controller.answered.promise;
    }

    // The id is per dialog, so it can't be written into the template.
    private static label(dialog: HTMLDialogElement): void {
        const label = dialog.querySelector("[data-dialog-label]");
        if (!label) return;
        label.id = `${dialog.id}-label`;
        dialog.setAttribute("aria-labelledby", label.id);
    }

    private static listenForClose<R>(
        dialog: HTMLDialogElement,
        controller: DialogController<R>,
    ): void {
        for (const closeButton of dialog.querySelectorAll("[data-dialog-close]")) {
            closeButton.addEventListener("click", () => {
                if (!controller.saving) {
                    dialog.close();
                }
            });
        }
        dialog.addEventListener("cancel", (event) => {
            if (controller.saving) {
                event.preventDefault();
            }
        });
        dialog.addEventListener("click", (event) => {
            const closes = controller.closesOnBackdropClick && !controller.saving;
            if (closes && DialogController.landedOnBackdrop(dialog, event)) {
                dialog.close();
            }
        });
        // Every way it closes ends here, so the promise resolves in one place.
        dialog.addEventListener("close", () => {
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
