import { Controller } from "django-website-widgets";
import { ReportCopyDialogController } from "../../widgets/report_copy_dialog/report_copy_dialog";

class Elements {
    reportButton: HTMLButtonElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.reportButton = root.querySelector('.copy-page__report');
    }
}

export class CopyPageController extends Controller {
    private elements = new Elements();
    private label = '';

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
        this.label = this.rootElement?.dataset.label ?? '';
    }

    public setState(): void {
    }

    protected initializeListeners(): void {
        // Rendered only for someone who may report, so it may not be there.
        this.elements.reportButton?.addEventListener('click', () => this.reportProblem());
    }

    private async reportProblem(): Promise<void> {
        const report = await ReportCopyDialogController.show({ label: this.label });
        if (report === null) return;
        // The server renders the new report in the history, and a retired copy without the button.
        window.location.reload();
    }
}
