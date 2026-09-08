<script lang="ts">
    import * as _ from "lodash-es"
    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import LikertHistogram from "./graph/LikertHistogram.svelte";
    import LikertBarChart from "./graph/LikertBarChart.svelte";
    import LikertMeanChart from "./graph/LikertMeanChart.svelte";
    import {
        formatNumber,
        getHighestHistogramValue,
        getHistogramMean,
        getSortMaturityLabel,
        getColourForMeanValue,
        getTextColourForMeanValue,
    } from "../misc.svelte.ts";

    type QM = {
        index: number;
        mean: number;
    }

    interface Props {
        config: SurveyConfig;
        surveyStats: SurveyStats | null;
        sectionIndex: number,
        fieldIndex: number,
        readinessDescriptions?: string[],
        useBarChart?: boolean,
        maxHistogramCount?: number
    }

    let {
        config,
        surveyStats,
        sectionIndex,
        fieldIndex,
        readinessDescriptions = [],
        useBarChart = true,
        maxHistogramCount = 0
    }: Props = $props();

    let sectionConfig = $derived(config?.sections?.[sectionIndex]);
    let fieldConfig = $derived(config?.sections?.[sectionIndex]?.fields?.[fieldIndex]);
    // Stats are optional throughout: a field whose answers are missing from the stored
    // responses has no histograms and no mean, and that must degrade rather than throw.
    let fieldStats = $derived(surveyStats?.sections?.[sectionIndex]?.fields?.[fieldIndex] ?? {});
    let histograms = $derived(fieldStats.histograms ?? []);
    let sublabels = $derived(fieldConfig?.sublabels ?? []);
    let questionMeanSorted: QM[] = $derived.by(() => {
        const qm = [];
        for (let i = 0; i < histograms.length; i++) {
            qm.push({
                index: i,
                mean: getHistogramMean(histograms[i])
            })
        }
        return _.orderBy(qm, ["mean"], ["asc"]);
    })
    let strongestAreas = $derived.by(() => {
        const strongestList = questionMeanSorted.slice(-2);
        return strongestList.map(qm => ({
            label: sublabels[qm.index],
            mean: qm.mean
        }));
    })
    let weakestAreas = $derived.by(() => {
        const weakestList = questionMeanSorted.slice(0, 2);
        return weakestList.map(qm => ({
            label: sublabels[qm.index],
            mean: qm.mean
        }));
    })
    // undefined when this field has no numeric answers, e.g. the stored responses are
    // missing this section or hold non-numeric values for it.
    let sectionMeanReadiness = $derived(fieldStats.mean);
    let readinessDescription = $derived(
        sectionMeanReadiness === undefined
            ? undefined
            : readinessDescriptions[Math.trunc(sectionMeanReadiness) - 1]
    );

</script>
{#if sectionMeanReadiness !== undefined}
    <h3>Summary <span class="badge badge-secondary bg-secondary">{sectionMeanReadiness.toFixed(0)}</span></h3>
    <p>
        Section {sectionConfig?.title} demonstrates an overall score <strong>
        of {sectionMeanReadiness.toFixed(2)} out of
        {getHighestHistogramValue(histograms[0] ?? [])}</strong> indicating
        maturity
        ranking of <strong>{getSortMaturityLabel(sectionMeanReadiness)}</strong>.
        {#if readinessDescription}
            The responses suggest that {readinessDescription}
        {/if}
    </p>
    <div class="progress">
        <div class="progress-bar bg-secondary" role="progressbar" style="width: {0.25*sectionMeanReadiness*100}%"
             aria-valuenow="{sectionMeanReadiness}" aria-valuemin="0" aria-valuemax="4">
            {sectionMeanReadiness.toFixed(1)} / 4
        </div>
    </div>
{:else}
    <h3>Summary</h3>
    <p>
        No overall score is available for section {sectionConfig?.title}, because the
        recorded answers for this section are missing or not numeric.
    </p>
{/if}
<h4>Areas of strength</h4>
<p>Areas of strength are demonstrated in the following questions:</p>
<ul>
    {#each strongestAreas as strongArea }
        <li>{strongArea.label} <span class="badge" style="background-color: {getColourForMeanValue(strongArea.mean)}; color: {getTextColourForMeanValue(strongArea.mean)};" title="Average score {strongArea.mean.toFixed(1)}/5">{strongArea.mean.toFixed(1)}</span></li>
    {/each}
</ul>
<h4>Areas for improvement</h4>
<p>
    Areas of improvements are identified in the following questions:
</p>
<ul>
    {#each weakestAreas as weakArea }
        <li>{weakArea.label} <span class="badge" style="background-color: {getColourForMeanValue(weakArea.mean)}; color: {getTextColourForMeanValue(weakArea.mean)};" title="Average score {weakArea.mean.toFixed(1)}/5">{weakArea.mean.toFixed(1)}</span></li>
    {/each}
</ul>
<h4>Mean scores by question</h4>
<p>The chart below shows the average (mean) score for each question in this section. Each bar represents the overall performance for that question, with colours indicating the maturity level achieved.</p>
<LikertMeanChart fieldConfig={fieldConfig}
                 fieldStats={fieldStats}>
</LikertMeanChart>
<h4>Response distribution</h4>
<p>The chart below shows the detailed breakdown of all responses for each question. Each bar is divided into segments representing the number of responses at each maturity level (Not Yet Planned, Planned, Early Progress, Substantial Progress, Established).</p>
{#if useBarChart}
    <LikertBarChart fieldConfig={fieldConfig}
                     fieldStats={fieldStats}
                     maxHistogramCount={maxHistogramCount}></LikertBarChart>
{:else}
    <LikertHistogram fieldConfig={fieldConfig}
                    fieldStats={fieldStats}
                    maxHistogramCount={maxHistogramCount}
                    sectionTitle={sectionConfig?.title}></LikertHistogram>
{/if}
