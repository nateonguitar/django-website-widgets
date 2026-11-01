import { Controller } from "django-website-widgets";
import { Theme } from "../../ts/theme";
// Types only: erased from the build, so main.js still doesn't contain Chart.js.
import type { Chart } from "chart.js";

class Elements {
    canvas: HTMLCanvasElement | null = null;
    spinner: HTMLElement | null = null;

    public findIn(root: HTMLElement | null): void {
        if (!root) return;
        this.canvas = root.querySelector('.my-history-page__canvas');
        this.spinner = root.querySelector('.my-history-page__chart-spinner');
    }
}

export class MyHistoryPageController extends Controller {
    private elements = new Elements();
    private labels: string[] = [];
    private counts: number[] = [];
    private chartReady = false;

    public async initState(): Promise<void> {
        this.elements.findIn(this.rootElement);
        this.initializeListeners();
        // Each a JSON list in a data- attribute on the root, written by MyHistoryPage.set_context().
        this.labels = JSON.parse(this.rootElement?.dataset.chartLabels ?? '[]');
        this.counts = JSON.parse(this.rootElement?.dataset.chartCounts ?? '[]');
    }

    public async afterFirstSetState(): Promise<void> {
        await this.drawChart();
    }

    public setState(): void {
        if (this.elements.spinner) {
            this.elements.spinner.hidden = this.chartReady;
        }
    }

    protected initializeListeners(): void {
    }

    private async drawChart(): Promise<void> {
        if (!this.elements.canvas) {
            return;
        }
        // A dynamic import: webpack puts Chart.js in its own chunk (static/chunks/), which only
        // this page downloads, rather than in main.js, which every page loads.
        const { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } = await import('chart.js');
        // Chart.js ships every chart type; registering only what this chart uses keeps the
        // chunk small.
        Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);
        const chart = new Chart(this.elements.canvas, {
            type: 'bar',
            data: {
                labels: this.labels,
                datasets: [{
                    label: 'Checkouts',
                    data: this.counts,
                }],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { autoSkip: true, maxTicksLimit: 12 } },
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                },
            },
        });
        this.colorChart(chart);
        // A canvas is drawn once with the colours it was given, so a theme change redraws it.
        Theme.onChange(() => this.colorChart(chart));
        this.chartReady = true;
        this.setState();
    }

    /** The theme's colours, read from its CSS variables, since a canvas can't use var(). */
    private colorChart(chart: Chart): void {
        const muted = Theme.color('--muted-text-color');
        const border = Theme.color('--border-color');
        chart.data.datasets[0].backgroundColor = Theme.color('--accent-color');
        for (const scale of [chart.options.scales!.x!, chart.options.scales!.y!]) {
            scale.ticks!.color = muted;
            scale.grid!.color = border;
        }
        chart.update();
    }
}
