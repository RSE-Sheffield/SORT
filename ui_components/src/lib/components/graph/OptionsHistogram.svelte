<script lang="ts">
    import {onMount} from "svelte";
    import {
        Chart,
        Colors,
        PieController,
        Legend,
        PointElement,
        ArcElement
    } from 'chart.js'

    Chart.register(
        Colors,
        PieController,
        Legend,
        PointElement,
        ArcElement
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
        fieldStats.histogram.map(value => {
            labels.push(value.option);
            data.push(value.count);
        });
        let datasets = [{
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
            type: 'pie',
            data: {
                labels: labels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
            }
        });

    })
</script>
<div>
    <canvas bind:this={chartContainer}></canvas>
</div>

