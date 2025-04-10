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
        PointElement

    } from 'chart.js'

    Chart.register(
        Colors,
        BarController,
        BarElement,
        CategoryScale,
        LinearScale,
        Legend,
        PointElement
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
    }

    let {fieldConfig, fieldStats}: LikertHistogramProps = $props();
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
                        position: "top"
                    },
                    y: {
                        beginAtZero: true,
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

