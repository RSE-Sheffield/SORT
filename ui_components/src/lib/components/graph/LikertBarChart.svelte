<script lang="ts">
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

    Chart.register(
        Colors,
        BarController,
        BarElement,
        CategoryScale,
        LinearScale,
        Legend,
        PointElement,
        Tooltip,
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
    let chartHeight = $derived(fieldConfig.sublabels.length * 2.5); // Reduced height since we're showing less data
    let chart: Chart | null = $state(null);
    let indexMean: IndexMean[] = $derived.by(() => {
        let ims: IndexMean[] = [];
        fieldStats.histograms.map((value, index) => {
            ims.push({
                index: index,
                mean: getHistogramMean(value)
            })
        });
        return ims;
    });

    function generateStats() {
        let labels = [];
        let meanValues = [];
        let backgroundColors = [];

        // Generate labels, mean values, and colors
        indexMean.map(im => {
            labels.push(fieldConfig.sublabels[im.index]);
            meanValues.push(im.mean);
            backgroundColors.push(getColourForMeanValue(im.mean));
        });

        // Single dataset with mean values
        const datasets = [{
            label: 'Mean Score',
            data: meanValues,
            backgroundColor: backgroundColors,
            borderWidth: 1,
            borderColor: backgroundColors.map(color => color), // Same as background or you could darken them
        }];

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
                        ...(maxHistogramCount > 0 && { max: maxHistogramCount })
                    },
                    y: {
                        ticks: {
                            callback: (value) => {
                                const maxCutoff = 80;
                                const labelValue: string = fieldConfig.sublabels[indexMean[value].index];
                                if (labelValue.length > maxCutoff)
                                    return labelValue.substring(0, maxCutoff) + "...";
                                else
                                    return labelValue;
                            }
                        }
                    }
                },
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // Hide legend since we only have one dataset
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Mean Score: ${context.parsed.x.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    })
</script>

<div style="height: {chartHeight}em;">
    <canvas bind:this={barChartContainer}></canvas>
</div>
