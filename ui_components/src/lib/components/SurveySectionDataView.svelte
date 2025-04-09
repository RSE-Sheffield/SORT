<script lang="ts">

    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import {TextType} from "../interfaces.ts";
    import {formatNumber, getHighestHistogramValue} from "../misc.svelte.ts";
    import LikertHistogram from "./graph/LikertHistogram.svelte";
    import OptionsHistogram from "./graph/OptionsHistogram.svelte";
    import CollapsibleCard from "./CollapsibleCard.svelte";
    import SortLikertStats from "./SortLikertStats.svelte";
    import ScalarHistogram from "./graph/ScalarHistogram.svelte";

    interface Props {
        config: SurveyConfig,
        surveyStats: SurveyStats,
        sectionIndex: number
    }

    let {config, surveyStats, sectionIndex = 0}: Props = $props();
    let sectionConfig = $derived(config.sections[sectionIndex]);

</script>
<div class="d-flex flex-wrap">

    {#each sectionConfig.fields as fieldConfig, fi}
        {#if fieldConfig.type === "likert" && sectionConfig.type === "sort"}
            <div class="mb-3 flex-grow-1 flex-fill w-100">

                <SortLikertStats
                        config={config}
                        surveyStats={surveyStats}
                        sectionIndex={sectionIndex}
                        fieldIndex={fi}>
                </SortLikertStats>
            </div>

        {:else if fieldConfig.type === "likert" }
            <div class="mb-3 flex-grow-1 flex-fill w-100">

                <LikertHistogram fieldConfig={fieldConfig}
                                 fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></LikertHistogram>
            </div>
        {/if}
        {#if fieldConfig.type === "radio" || fieldConfig.type === "select" || fieldConfig.type === "checkbox"}
            <div class="card mb-3 w-50">
                <div class="card-header">
                    <h5>{fieldConfig.label}</h5>
                </div>
                <div class="card-body">
                    <OptionsHistogram fieldConfig={fieldConfig}
                              fieldStats={surveyStats.sections[sectionIndex].fields[fi]}></OptionsHistogram>
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
            <div class="mb-3 flex-grow-1 w-100" >
                <CollapsibleCard
                        title={`${fieldConfig.label} (${surveyStats.sections[sectionIndex].fields[fi].values.length})`}
                        startCollapsed={true}
                >
                    {#snippet content()}
                        <ul class="list-group">
                            {#each surveyStats.sections[sectionIndex].fields[fi].values as text}

                                <li class="list-group-item">{text}</li>
                            {/each}
                        </ul>
                    {/snippet}
                </CollapsibleCard>
            </div>
        {/if}
    {/each}
</div>
