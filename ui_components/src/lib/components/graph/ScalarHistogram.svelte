<script lang="ts">
    import * as _ from "lodash-es"
    import {onMount} from "svelte";
    import {
        Chart,
        Colors,
        LineController,
        LinearScale,
        LineElement,
        Legend,
        PointElement
    } from 'chart.js'

    Chart.register(
        Colors,
        LineController,
        LineElement,
        LinearScale,
        Legend,
        PointElement
    );
    import type {FieldConfig, FieldStats} from "../../interfaces.ts";


    interface Props {
        fieldConfig: FieldConfig;
        fieldStats: FieldStats;
    }

    let {fieldConfig, fieldStats}: Props = $props();
    let chartContainer: HTMLCanvasElement = $state()
    let chart: Chart | null = $state(null);

    function generateStats() {
        let labels = [];
        let data = [];

        const dataMap = _.countBy(fieldStats.values.map(Number), Math.floor);
        for (let key in dataMap) {
            let value = dataMap[key];
            labels.push(key);
            data.push(value);
        }

        let datasets = [{
            label: "Number of responses",
            data: data,
            borderWidth: 1,
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
        chart = new Chart(chartContainer, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            text: fieldConfig.label,
                            display: true,
                        },
                        ticks: {
                            stepSize: 1,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            text: "# of responses",
                            display: true
                        },
                        ticks: {
                            stepSize: 1,
                        }

                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

    })
</script>
<div class="h-100">
    <canvas bind:this={chartContainer}></canvas>
</div>

