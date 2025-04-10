<script lang="ts">
    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import {formatNumber, getColourForMeanValue, getTextColourForMeanValue} from "../misc.svelte.ts";
    interface Props {
        config: SurveyConfig;
        surveyStats: SurveyStats;
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
<table class="table table-bordered">
    <thead>
    <tr>
        {#each sectionTitles as title}
            <th scope="col" style="text-align: center">{title}</th>
        {/each}
    </tr>
    </thead>
    <tbody>
    <tr>
        {#each sectionMean as mean}
            <td style="text-align: center; background: {getColourForMeanValue(mean)};">
                <strong style="color: {getTextColourForMeanValue(mean)}">{formatNumber(mean)}</strong>
            </td>
        {/each}
    </tr>

    </tbody>
</table>
