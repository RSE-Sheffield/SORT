<script lang="ts">

    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import {TextType} from "../interfaces.ts";
    import LikertHistogram from "./graph/LikertHistogram.svelte";
    import LikertBarChart from "./graph/LikertBarChart.svelte";
    import OptionsPieChart from "./graph/OptionsPieChart.svelte";
    import CollapsibleCard from "./CollapsibleCard.svelte";
    import SortLikertStats from "./SortLikertStats.svelte";
    import ScalarHistogram from "./graph/ScalarHistogram.svelte";

    interface Props {
        config: SurveyConfig,
        surveyStats: SurveyStats | null,
        sectionIndex: number,
        readinessDescriptions: string[],
        useBarChart: boolean
    }

    let {config, surveyStats, sectionIndex = 0, readinessDescriptions, useBarChart = false}: Props = $props();
    let sectionConfig = $derived(config.sections[sectionIndex]);

</script>
{#if surveyStats && config}
    <div class="d-flex flex-wrap">
        {#each sectionConfig.fields as fieldConfig, fi (fi)}
            {#if !fieldConfig.disabled}
            {#if fieldConfig.type === "likert" && sectionConfig.type === "sort"}
                <div class="mb-3 flex-grow-1 flex-fill w-100">

                    <SortLikertStats
                            config={config}
                            surveyStats={surveyStats}
                            sectionIndex={sectionIndex}
                            fieldIndex={fi}
                            readinessDescriptions={readinessDescriptions}
                            useBarChart={useBarChart}>
                    </SortLikertStats>
                </div>

            {:else if fieldConfig.type === "likert" }
                <div class="mb-3 flex-grow-1 flex-fill w-100">
                    {#if useBarChart}
                    <LikertBarChart fieldConfig={fieldConfig}
                                     fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></LikertBarChart>
                    {:else}
                    <LikertHistogram fieldConfig={fieldConfig}
                                     fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></LikertHistogram>
                    {/if}
                </div>
            {/if}
            {#if fieldConfig.type === "radio" || fieldConfig.type === "select" || fieldConfig.type === "checkbox"}
                <div class="card mb-3 w-50">
                    <div class="card-header">
                        <h5>{fieldConfig.label}</h5>
                    </div>
                    <div class="card-body">
                        <OptionsPieChart fieldConfig={fieldConfig}
                                          fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></OptionsPieChart>
                    </div>
                </div>
            {/if}
            {#if fieldConfig.type === "text" && (fieldConfig.textType === TextType.integer || fieldConfig.textType === TextType.decimals)}
                <div class="card mb-3 w-50">
                    <div class="card-header">
                        <h5>{fieldConfig.label}</h5>
                    </div>
                    <div class="card-body">
                        <ScalarHistogram fieldConfig={fieldConfig}
                                         fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></ScalarHistogram>
                    </div>
                </div>
            {/if}
            {#if fieldConfig.type === "textarea"}
                <div class="mb-3 flex-grow-1 w-100">
                    <CollapsibleCard
                            title={`${fieldConfig.label} (${surveyStats.sections[sectionIndex].fields[fi].values.length})`}
                            startCollapsed={true}
                    >
                        {#snippet content()}
                            <ul class="list-group">
                                {#each surveyStats.sections[sectionIndex].fields[fi].values as text, index (index)}

                                    <li class="list-group-item">{text}</li>
                                {/each}
                            </ul>
                        {/snippet}
                    </CollapsibleCard>
                </div>
            {/if}
            {/if}
        {/each}
    </div>
{:else }
    <p>Statistics not available</p>
{/if}
