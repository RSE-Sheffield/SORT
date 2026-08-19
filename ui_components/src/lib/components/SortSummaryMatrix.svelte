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

    type SectionSummary = {
        title: string;
        mean?: number;
    };

    // Derived rather than computed at init: this component is mounted directly by main.ts
    // with whatever generateStatsFromSurveyResponses() returned, which is null when there
    // are no responses. Reading surveyStats eagerly crashed the whole report.
    let sectionSummaries: SectionSummary[] = $derived.by(() => {
        const summaries: SectionSummary[] = [];
        const sections = config?.sections ?? [];
        for (let i = 0; i < sections.length; i++) {
            if (sections[i].type !== "sort") continue;
            summaries.push({
                title: sections[i].title,
                mean: sectionMean(i),
            });
        }
        return summaries;
    });

    /**
     * The mean score for a section: the first field that has one.
     *
     * A section's scored field is normally its first, but a survey configuration is free
     * to order fields differently, and a field whose answers are missing or non-numeric
     * has no mean at all.
     */
    function sectionMean(sectionIndex: number): number | undefined {
        const fields = surveyStats?.sections?.[sectionIndex]?.fields ?? [];
        return fields.find(fieldStats => typeof fieldStats.mean === "number")?.mean;
    }
</script>
{#if surveyStats && sectionSummaries.length > 0}
<table class="table table-bordered">
    <thead>
    <tr>
        {#each sectionSummaries as summary, index (index)}
            <th scope="col" style="text-align: center">{summary.title}</th>
        {/each}
    </tr>
    </thead>
    <tbody>
    <tr>
        {#each sectionSummaries as summary, index (index)}
            <td style="text-align: center; background: {getColourForMeanValue(summary.mean)};">
                <strong style="color: {getTextColourForMeanValue(summary.mean)}">
                    {getSortMaturityLabel(summary.mean)}{#if summary.mean !== undefined} ({formatNumber(summary.mean)}){/if}
                </strong>
            </td>
        {/each}
    </tr>

    </tbody>
</table>
{:else }
<p>Statistics not available</p>
{/if}
