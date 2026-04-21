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
        Tooltip,
        ChartDataLabels,
    );
    import type {FieldConfig, FieldStats} from "../../interfaces.ts";
    import {getColourForMeanValue, getHistogramMean, getSortMaturityLabel} from "../../misc.svelte.js";

    type IndexMean = {
        index: number;
        mean: number;
    }

    interface LikertMeanChartProps {
        fieldConfig: FieldConfig;
        fieldStats: FieldStats;
    }

    let {fieldConfig, fieldStats}: LikertMeanChartProps = $props();
    let barChartContainer: HTMLCanvasElement = $state()
    const barThickness = 30;  // Match the barThickness in LikertHistogram
    let chartHeightPx = $derived((fieldConfig.sublabels.length * (barThickness + 10)) + 150); // Match LikertHistogram calculation
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
            borderColor: backgroundColors.map(color => color),
            barThickness: barThickness,  // Fixed pixel height for bars
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
                        max: 4,
                        title: {
                            display: true,
                            text: 'Mean Score'
                        }
                    },
                    y: {
                        ticks: {
                            autoSkip: false,
                            callback: function(value) {
                                const labelValue: string = fieldConfig.sublabels[indexMean[value].index];
                                const maxCharsPerLine = 40;
                                const maxLines = 2;

                                // Split long labels into multiple lines with truncation
                                if (labelValue.length <= maxCharsPerLine) {
                                    return labelValue;
                                }

                                const words = labelValue.split(' ');
                                const lines: string[] = [];
                                let currentLine = '';

                                for (const word of words) {
                                    if (lines.length >= maxLines) break;

                                    const testLine = currentLine + (currentLine ? ' ' : '') + word;
                                    if (testLine.length <= maxCharsPerLine) {
                                        currentLine = testLine;
                                    } else {
                                        if (currentLine) {
                                            lines.push(currentLine);
                                            currentLine = word;
                                        } else {
                                            // Word is too long, truncate it
                                            lines.push(word.substring(0, maxCharsPerLine - 3) + '...');
                                            currentLine = '';
                                        }
                                    }
                                }

                                if (currentLine && lines.length < maxLines) {
                                    lines.push(currentLine);
                                } else if (lines.length >= maxLines && currentLine) {
                                    // Truncate last line if we have more content
                                    lines[maxLines - 1] = lines[maxLines - 1].substring(0, maxCharsPerLine - 3) + '...';
                                }

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
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const meanValue = context.parsed.x;
                                const maturityLabel = getSortMaturityLabel(meanValue);
                                return `Mean Score: ${meanValue.toFixed(2)} (${maturityLabel})`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        font: {
                            weight: 'bold',
                            size: 11
                        },
                        formatter: (value, context) => {
                            return getSortMaturityLabel(value);
                        },
                        anchor: 'center',
                        align: 'center',
                    }
                }
            }
        });
    })
</script>

<div style="height: {chartHeightPx}px;">
    <canvas bind:this={barChartContainer}></canvas>
</div>
