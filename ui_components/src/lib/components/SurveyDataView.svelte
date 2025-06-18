<script lang="ts">
    import type {SurveyConfig, SurveyResponseBatch, SurveyStats} from "../interfaces.ts";
    import {generateStatsFromSurveyResponses} from "../misc.svelte.ts";
    import SurveySectionDataView from "./SurveySectionDataView.svelte";
    import SortSummaryMatrix from "./SortSummaryMatrix.svelte";
    import SurveyDemographicFilters from "./SurveyDemographicFilters.svelte";

    interface SurveyDataViewProps {
        config: SurveyConfig;
        responses: SurveyResponseBatch
    }

    let {config, responses}: SurveyDataViewProps = $props();
    let filteredResponses = $state(responses);

    //Calculate section stats
    let surveyStats: SurveyStats | null = $derived.by(() => {

        if (config === null ||
            responses === null ||
            responses === undefined ||
            responses.length < 1)
            return null;

        return generateStatsFromSurveyResponses(config, filteredResponses);
    })

    function handleFilterChange(changedFilteredResponses: SurveyResponseBatch) {
        filteredResponses = changedFilteredResponses;
    }


</script>
<div>
    {#if config && responses }
        <div class="card mb-3">
            <div class="card-header">
                <h3>Survey data filters</h3>
            </div>
            <div class="card-body">
                <p>
                    Use the controls below to filter the survey responses.
                </p>
                <SurveyDemographicFilters
                        config={config}
                        responses={responses}
                        onFilterChange={handleFilterChange}
                >

                </SurveyDemographicFilters>
            </div>
        </div>
    {/if}
    {#if config && surveyStats}

        <div class="card mb-3">
            <div class="card-header"><h3>Summary Ranking Matrix</h3></div>
            <div class="card-body">
                <p>Summary of survey participant's overall average perception for each section.</p>
                <SortSummaryMatrix config={config} surveyStats={surveyStats}></SortSummaryMatrix>
            </div>
        </div>

        {#each config.sections as sectionConfig, si (si)}
            {#if sectionConfig.type !== "consent"}
                <div class="card mb-3">
                    <div class="card-header">
                        <h3>{sectionConfig.title}</h3>
                    </div>
                    <div class="card-body">
                        <SurveySectionDataView
                                config={config}
                                surveyStats={surveyStats}
                                sectionIndex={si}>
                        </SurveySectionDataView>
                    </div>
                </div>
            {/if}
        {/each}


    {:else}
        <p>No statistics available.</p>
    {/if}
</div>
