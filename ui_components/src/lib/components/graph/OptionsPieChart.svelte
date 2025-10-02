<script lang="ts">
    import {onMount} from "svelte";
    import {
        Chart,
        Colors,
        PieController,
        Legend,
        PointElement,
        ArcElement,
        Tooltip,

    } from 'chart.js'

    Chart.register(
        Colors,
        PieController,
        Legend,
        PointElement,
        ArcElement,
        Tooltip,
    );

    import type {FieldConfig, FieldStats} from "../../interfaces.ts";


    interface Props {
        fieldConfig: FieldConfig;
        fieldStats: FieldStats;
    }

    let {fieldConfig, fieldStats}: Props = $props();
    let pieChartContainer: HTMLCanvasElement = $state()
    let pieChart: Chart | null = $state(null);

    // Extended color palette with 30 distinct colors
    const colorPalette = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#E74C3C', '#C9CBCF', '#1ABC9C', '#F39C12',
        '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6',
        '#EF4444', '#D35400', '#059669', '#7C3AED', '#DC2626',
        '#06B6D4', '#84CC16', '#F97316', '#6366F1', '#14B8A6',
        '#A855F7', '#22C55E', '#EAB308', '#2563EB', '#BE185D'
    ];

    function generatePieChartData() {
        let labels = [];
        let data = [];
        fieldStats.histogram.map(value => {
            labels.push(value.option);
            data.push(value.count);
        });

        // Generate background colors cycling through the palette
        const backgroundColor = data.map((_, index) => colorPalette[index % colorPalette.length]);

        let datasets = [{
            data: data,
            backgroundColor: backgroundColor,
            borderWidth: 1,
        }];

        return {labels, datasets};
    }

    $effect(() => {
        let {labels, datasets} = generatePieChartData();
        if (pieChart) {
            pieChart.data.labels = labels;
            pieChart.data.datasets = datasets;
            pieChart.update();
        }
    })

    onMount(() => {
        let {labels, datasets} = generatePieChartData();
        pieChart = new Chart(pieChartContainer, {
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
    <canvas bind:this={pieChartContainer}></canvas>
</div>

