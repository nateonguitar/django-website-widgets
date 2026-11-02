import { DialogController } from "django-website-widgets";
import { ApiError } from "../../ts/api/api-service";
import { CopyApiService, ReportCopyRequest, ReportCopyResponse } from "../../ts/api/copy-api-service";

class Elements {
    title: HTMLElement | null = null;
    form: HTMLFormElement | null = null;
    kindInputs: HTMLInputElement[] = [];
    notes: HTMLTextAreaElement | null = null;
    unrecoverable: HTMLInputElement | null = null;
    fieldErrors: HTMLElement[] = [];
    message: HTMLElement | null = null;
    sendButton: HTMLButtonElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.title = root.querySelector('.report-copy-dialog__title');
        this.form = root.querySelector('.report-copy-dialog__form');
        this.kindInputs = Array.from(root.querySelectorAll('input[name="kind"]'));
        this.notes = root.querySelector('textarea[name="notes"]');
        this.unrecoverable = root.querySelector('input[name="unrecoverable"]');
        this.fieldErrors = Array.from(root.querySelectorAll('.report-copy-dialog__field-error'));
        this.message = root.querySelector('.report-copy-dialog__message');
        this.sendButton = root.querySelector('.report-copy-dialog__send');
    }
}

/** FieldErrorsResponseDto's errors, for the fields this form has. */
class ReportCopyErrors {
    kind?: string;
    notes?: string;
}

/**
 * Reports a problem with one copy: `const report = await ReportCopyDialogController.show({ label })`
 * answers the saved report, or null when cancelled.
 */
export class ReportCopyDialogController extends DialogController<ReportCopyResponse | null> {
    private elements = new Elements();
    // Stays null unless the report is saved, so Cancel or Escape answers null.
    private saved: ReportCopyResponse | null = null;
    private errors = new ReportCopyErrors();
    private message = '';

    constructor(private label: string) {
        super();
        // A stray click outside would throw away what was typed.
        this.closesOnBackdropClick = false;
    }

    public static show({ label }: { label: string }): Promise<ReportCopyResponse | null> {
        return DialogController.openDialog(
            new ReportCopyDialogController(label),
            "#report-copy-dialog-template",
        );
    }

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
    }

    protected initializeListeners(): void {
        this.elements.form?.addEventListener('submit', (event) => {
            event.preventDefault();
            this.send();
        });
    }

    public setState(): void {
        const elements = this.elements;
        if (elements.title) {
            elements.title.textContent = `What's wrong with ${this.label}?`;
        }
        for (const fieldError of elements.fieldErrors) {
            const field = fieldError.dataset.field as keyof ReportCopyErrors;
            fieldError.textContent = this.errors[field] ?? '';
        }
        if (elements.message) {
            elements.message.textContent = this.message;
        }
        if (elements.sendButton) {
            elements.sendButton.disabled = this.saving;
            elements.sendButton.textContent = this.saving ? 'Sending…' : 'Send report';
        }
    }

    private readForm(): ReportCopyRequest {
        const report = new ReportCopyRequest();
        report.kind = this.elements.kindInputs.find((input) => input.checked)?.value ?? '';
        report.notes = this.elements.notes?.value ?? '';
        report.unrecoverable = this.elements.unrecoverable?.checked ?? false;
        return report;
    }

    private async send(): Promise<void> {
        // Holds Escape and Cancel off until the request finishes.
        this.saving = true;
        this.errors = new ReportCopyErrors();
        this.message = '';
        this.setState();
        try {
            const result = await CopyApiService.instance.reportCopy(this.label, this.readForm());
            if (result.status === 201) {
                // Stored before closing: closing resolves the caller's promise with answer().
                this.saved = result.body;
                this.saving = false;
                this.dialog?.close();
                return;
            }
            if (result.status === 400) {
                this.errors = Object.assign(new ReportCopyErrors(), result.body.errors);
            } else {
                this.message = result.body.message;
            }
        } catch (error) {
            this.message = ApiError.messageFor(error);
        }
        this.saving = false;
        this.setState();
    }

    protected answer(): ReportCopyResponse | null {
        return this.saved;
    }
}
