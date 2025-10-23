<script lang="ts">
    import * as _ from "lodash-es";
    import {onMount} from "svelte";
    import {
        Chart,
        Colors,
        BarController,
        CategoryScale,
        LinearScale,
        BarElement,
        Legend,
        PointElement,
        Tooltip,

    } from 'chart.js'
    import ChartDataLabels from 'chartjs-plugin-datalabels';

    Chart.register(
        Colors,
        BarController,
        BarElement,
        CategoryScale,
        LinearScale,
        Legend,
        PointElement,
        Tooltip,
        ChartDataLabels,
    );
    import type {FieldConfig, FieldStats} from "../../interfaces.ts";
    import {getColourForMeanValue, getHistogramMean} from "../../misc.svelte.js";

    type IndexMean = {
        index: number;
        mean: number;
    }

    interface LikertHistogramProps {
        fieldConfig: FieldConfig;
        fieldStats: FieldStats;
        maxHistogramCount?: number;
    }

    let {fieldConfig, fieldStats, maxHistogramCount = 0}: LikertHistogramProps = $props();
    let barChartContainer: HTMLCanvasElement = $state()
    let chartHeight = $derived(fieldConfig.sublabels.length * 5);
    let chart: Chart | null = $state(null);
    let sortByMean = $state(false);
    let sortAscending = $state(true);
    let indexMean: IndexMean[] = $derived.by(() => {
        let ims: IndexMean[] = [];
        fieldStats.histograms.map((value, index) => {
            ims.push({
                index: index,
                mean: getHistogramMean(value)
            })
        });

        if (sortByMean) {
            let sortOrder: (boolean | "asc" | "desc")[] = ["asc", "asc"];
            if (!sortAscending) sortOrder = ["desc", "desc"];
            ims = _.orderBy(ims, ["mean", "index"], sortOrder);
        }
        return ims;
    });

    function generateStats() {

        let labels = [];
        let datasets = []

        // Sorted labels
        indexMean.map(im => {
            labels.push(fieldConfig.sublabels[im.index]);
        });

        // Sorted data
        fieldConfig.options.map((value, optionIndex) => {
            const values: number[] = [];
            for (let i = 0; i < indexMean.length; i++) {
                const im = indexMean[i];
                values.push(fieldStats.histograms[im.index][optionIndex].count);
            }
            const colour = getColourForMeanValue(Number(value));

            datasets.push({
                label: value,
                data: values,
                borderWidth: 1,
                backgroundColor: colour,
            })
        })
        return {labels, datasets};
    }

    $effect(() => {
        let {labels, datasets} = generateStats();
        if (chart) {
            chart.data.labels = labels;
            chart.data.datasets = datasets;
            chart.update();
        }
    })

    onMount(() => {
        let {labels, datasets} = generateStats();


        chart = new Chart(barChartContainer, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets,
            },
            options: {
                scales: {
                    x: {
                        position: "top",
                        beginAtZero: true,
                        min: 0,
                        stacked: true,
                        ...(maxHistogramCount > 0 && { max: maxHistogramCount })
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        ticks: {
                            callback: function(value) {
                                const labelValue: string = fieldConfig.sublabels[indexMean[value].index];
                                const maxCharsPerLine = 50;

                                // Split long labels into multiple lines
                                if (labelValue.length <= maxCharsPerLine) {
                                    return labelValue;
                                }

                                const words = labelValue.split(' ');
                                const lines: string[] = [];
                                let currentLine = '';

                                for (const word of words) {
                                    const testLine = currentLine + (currentLine ? ' ' : '') + word;
                                    if (testLine.length <= maxCharsPerLine) {
                                        currentLine = testLine;
                                    } else {
                                        if (currentLine) lines.push(currentLine);
                                        currentLine = word;
                                    }
                                }
                                if (currentLine) lines.push(currentLine);

                                return lines;
                            }
                        }
                    }
                },
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        title: {
                            display: true,
                            text: 'Score'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const score = context.dataset.label;
                                const count = context.parsed.x;
                                return `Score ${score}: ${count} responses`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        font: {
                            weight: 'bold',
                            size: 12
                        },
                        formatter: (value, context) => {
                            // Only show label if the segment is large enough
                            return value > 0 ? value : '';
                        },
                        anchor: 'center',
                        align: 'center',
                    }
                }
            }
        });

    })
</script>
<div class="btn-group mb-3 sorting-control" role="group" aria-label="Choose how the graph is sorted">
    <button
            class={{
              "btn": true,
              "btn-sm": true,
              "btn-primary": !sortByMean,
              "btn-outline-primary": sortByMean}}
            onclick={()=>{sortByMean = false;}}
    >
        Sort by question order
    </button>
    <button
            class={{
              "btn": true,
              "btn-sm": true,
              "btn-primary": sortByMean && sortAscending,
              "btn-outline-primary": !(sortByMean && sortAscending)}}
            onclick={()=>{sortByMean = true; sortAscending=true;}}
    >
        <i class='bx bx-sort-up'></i>Sort by lowest mean score
    </button>
    <button
            class={{
              "btn": true,
              "btn-sm": true,
              "btn-primary": sortByMean && !sortAscending,
              "btn-outline-primary": !(sortByMean && !sortAscending)}}
            onclick={()=>{sortByMean = true; sortAscending=false;}}
    >
        <i class='bx bx-sort-down'></i>Sort by highest mean score
    </button>

</div>
<div style="height: {chartHeight}em;">
    <canvas bind:this={barChartContainer}></canvas>
</div>

