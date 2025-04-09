<script lang="ts">
    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import LikertHistogram from "./graph/LikertHistogram.svelte";
    import {generateStatsFromSurveyResponses} from "../misc.svelte.ts";
    import OptionsHistogram from "./graph/OptionsHistogram.svelte";
    import CollapsibleCard from "./CollapsibleCard.svelte";
    import SurveySectionDataView from "./SurveySectionDataView.svelte";
    import SortSummaryMatrix from "./SortSummaryMatrix.svelte";
    import SurveyDemographicFilters from "./SurveyDemographicFilters.svelte";

    interface SurveyDataViewProps {
        config: SurveyConfig;
        responses: []
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

    function handleFilterChange(changedFilteredResponses) {
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


        {#each config.sections as sectionConfig, si}
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

        <div class="card mb-3">
            <div class="card-header"><h3>Summary Ranking Matrix</h3></div>
            <div class="card-body">
                <p>Summary of survey participant's overall average perception for each section.</p>
                <SortSummaryMatrix config={config} surveyStats={surveyStats}></SortSummaryMatrix>
            </div>
        </div>
    {:else}
        <p>No statistics available.</p>
    {/if}
</div>
