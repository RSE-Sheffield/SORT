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
        surveyStats: SurveyStats;
        sectionIndex: number,
        fieldIndex: number,
        readinessDescriptions: string[],
        useBarChart: boolean,
        maxHistogramCount: number
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

    let sectionConfig = $derived(config.sections[sectionIndex]);
    let fieldConfig = $derived(config.sections[sectionIndex].fields[fieldIndex]);
    let questionMeanSorted: QM[] = $derived.by(() => {
        const qm = [];
        for (let i = 0; i < surveyStats.sections[sectionIndex].fields[fieldIndex].histograms.length; i++) {
            qm.push({
                index: i,
                mean: getHistogramMean(surveyStats.sections[sectionIndex].fields[fieldIndex].histograms[i])
            })
        }
        return _.orderBy(qm, ["mean"], ["asc"]);
    })
    let strongestAreas = $derived.by(() => {
        const strongestList = questionMeanSorted.slice(-2);
        return strongestList.map(qm => ({
            label: fieldConfig.sublabels[qm.index],
            mean: qm.mean
        }));
    })
    let weakestAreas = $derived.by(() => {
        const weakestList = questionMeanSorted.slice(0, 2);
        return weakestList.map(qm => ({
            label: fieldConfig.sublabels[qm.index],
            mean: qm.mean
        }));
    })
    const sectionMeanReadiness: number = surveyStats.sections[sectionIndex].fields[fieldIndex].mean;
    const sectionMeanReadinessInt: bigint = parseInt(sectionMeanReadiness);
    const readinessDescription: string = readinessDescriptions[sectionMeanReadinessInt - 1];

</script>
<h3>Summary <span class="badge badge-secondary bg-secondary">{sectionMeanReadiness.toFixed(0)}</span></h3>
<p>
    Section {sectionConfig.title} demonstrates an overall score <strong>
    of {sectionMeanReadiness.toFixed(2)} out of
    {getHighestHistogramValue(surveyStats.sections[sectionIndex].fields[fieldIndex].histograms[0])}</strong> indicating
    maturity
    ranking of <strong>{getSortMaturityLabel(surveyStats.sections[sectionIndex].fields[fieldIndex].mean)}</strong>.
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
                 fieldStats={surveyStats.sections[sectionIndex].fields[fieldIndex]}>
</LikertMeanChart>
<h4>Response distribution</h4>
<p>The chart below shows the detailed breakdown of all responses for each question. Each bar is divided into segments representing the number of responses at each maturity level (Not Yet Planned, Planned, Early Progress, Substantial Progress, Established).</p>
{#if useBarChart}
    <LikertBarChart fieldConfig={fieldConfig}
                     fieldStats={surveyStats.sections[sectionIndex].fields[fieldIndex]}
                     maxHistogramCount={maxHistogramCount}></LikertBarChart>
{:else}
    <LikertHistogram fieldConfig={fieldConfig}
                    fieldStats={surveyStats.sections[sectionIndex].fields[fieldIndex]}
                    maxHistogramCount={maxHistogramCount}
                    sectionTitle={sectionConfig.title}></LikertHistogram>
{/if}
