<script lang="ts">
    import {onMount} from "svelte";
    import {
        Chart,
        BarController,
        BarElement,
        CategoryScale,
        LinearScale,
        LineController,
        LineElement,
        PointElement,
        Tooltip,
    } from 'chart.js'
    import type {UsageTrendRow, UsageTrendSeries} from "../../interfaces.ts";

    Chart.register(
        BarController,
        BarElement,
        CategoryScale,
        LinearScale,
        LineController,
        LineElement,
        PointElement,
        Tooltip,
    );

    interface UsageTrendsChartProps {
        trends: UsageTrendRow[];
    }

    let {trends}: UsageTrendsChartProps = $props();

    // One small chart per series, because the scales differ too much to share an axis
    const SERIES: { key: UsageTrendSeries, label: string }[] = [
        {key: "users", label: "Users"},
        {key: "organisations", label: "Organisations"},
        {key: "surveys", label: "Surveys"},
        {key: "responses", label: "Responses"},
    ];
    const COLOUR = "#2a78d6";

    let cumulative = $state(false);
    let canvases: HTMLCanvasElement[] = $state([]);
    let charts: Chart[] = [];

    function getValues(key: UsageTrendSeries): number[] {
        return trends.map(row => cumulative ? row[`${key}_total`] : row[key]);
    }

    function buildChart(canvas: HTMLCanvasElement, key: UsageTrendSeries, label: string): Chart {
        return new Chart(canvas, {
            type: cumulative ? 'line' : 'bar',
            data: {
                labels: trends.map(row => row.month),
                datasets: [{
                    label: label,
                    data: getValues(key),
                    backgroundColor: COLOUR,
                    borderColor: COLOUR,
                    borderWidth: 2,
                    borderRadius: 4,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {mode: 'index', intersect: false},
                scales: {
                    x: {grid: {display: false}, ticks: {maxTicksLimit: 8}},
                    y: {beginAtZero: true, ticks: {precision: 0}},
                },
                plugins: {
                    legend: {display: false},
                    // Registered globally by other SORT charts; not wanted here
                    datalabels: {display: false},
                },
            },
        });
    }

    function render() {
        charts.forEach(chart => chart.destroy());
        charts = SERIES.map((series, index) => buildChart(canvases[index], series.key, series.label));
    }

    onMount(() => {
        render();
        return () => charts.forEach(chart => chart.destroy());
    });

    function setCumulative(value: boolean) {
        cumulative = value;
        render();
    }
</script>

<div class="btn-group btn-group-sm mb-3" role="group" aria-label="Trend view">
    <input type="radio" class="btn-check" name="usage-trend-view" id="usage-trend-monthly" autocomplete="off"
           checked={!cumulative} onchange={() => setCumulative(false)}>
    <label class="btn btn-outline-primary" for="usage-trend-monthly">New per month</label>
    <input type="radio" class="btn-check" name="usage-trend-view" id="usage-trend-cumulative" autocomplete="off"
           checked={cumulative} onchange={() => setCumulative(true)}>
    <label class="btn btn-outline-primary" for="usage-trend-cumulative">Running total</label>
</div>

<div class="row g-4">
    {#each SERIES as series, index (series.key)}
        <div class="col-md-6">
            <h3 class="h6">{series.label}</h3>
            <div style="height: 220px;">
                <canvas bind:this={canvases[index]}>
                    {series.label}, {cumulative ? 'running total' : 'new per month'}. See the data table below.
                </canvas>
            </div>
        </div>
    {/each}
</div>
