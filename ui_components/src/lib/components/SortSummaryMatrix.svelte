<script lang="ts">
    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import {
        formatNumber,
        getColourForMeanValue,
        getSortMaturityLabel,
        getTextColourForMeanValue
    } from "../misc.svelte.ts";
    interface Props {
        config: SurveyConfig;
        surveyStats: SurveyStats | null;
    }
    let {config, surveyStats}: Props = $props();

    const sectionTitles: string[] = [];
    const sectionMean: number[] = [];

    for (let i = 0; i < config.sections.length; i++) {
        if (config.sections[i].type === "sort") {
            sectionTitles.push(config.sections[i].title);
            sectionMean.push(surveyStats.sections[i].fields[0].mean);
        }
    }


</script>
{#if surveyStats && config}
<table class="table table-bordered">
    <thead>
    <tr>
        {#each sectionTitles as title, index (index)}
            <th scope="col" style="text-align: center">{title}</th>
        {/each}
    </tr>
    </thead>
    <tbody>
    <tr>
        {#each sectionMean as mean, index (index)}
            <td style="text-align: center; background: {getColourForMeanValue(mean)};">
                <strong style="color: {getTextColourForMeanValue(mean)}">{getSortMaturityLabel(mean)} ({formatNumber(mean)})</strong>
            </td>
        {/each}
    </tr>

    </tbody>
</table>
{:else }
<p>Statistics not available</p>
{/if}
