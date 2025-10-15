<script lang="ts">
    import type {SurveyConfig, SurveyResponseBatch, SurveyStats} from "../interfaces.ts";
    import {generateStatsFromSurveyResponses} from "../misc.svelte.ts";
    import SurveyDemographicFilters from "./SurveyDemographicFilters.svelte";
    import CollapsibleCard from "./CollapsibleCard.svelte";
    import SortSummaryMatrix from "./SortSummaryMatrix.svelte";
    import SurveySectionDataView from "./SurveySectionDataView.svelte";

    interface SurveyReportAppProps {
        config: SurveyConfig;
        responses: SurveyResponseBatch;
        csvDownloadUrl: string;
        excelDownloadUrl: string;
    }

    let {config, responses, csvDownloadUrl, excelDownloadUrl}: SurveyReportAppProps = $props();
    let filteredResponses = $state(responses);

    // Calculate section stats based on filtered responses
    let surveyStats: SurveyStats | null = $derived.by(() => {
        if (config === null ||
            responses === null ||
            responses === undefined ||
            responses.length < 1)
            return null;

        return generateStatsFromSurveyResponses(config, filteredResponses);
    });

    function handleFilterChange(changedFilteredResponses: SurveyResponseBatch) {
        filteredResponses = changedFilteredResponses;
    }
</script>

<div class="survey-report-container">
    {#if config && responses}
        <CollapsibleCard title="Survey data filters" startCollapsed={true}>
            {#snippet content()}
                <p>
                    Use the controls below to filter the survey responses shown in this report.
                    Filters will also apply to exported data.
                </p>
                <SurveyDemographicFilters
                        config={config}
                        responses={responses}
                        onFilterChange={handleFilterChange}
                />
            {/snippet}
        </CollapsibleCard>

        <div class="mb-3">
            <strong>Responses shown: {filteredResponses.length} of {responses.length}</strong>
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
                <div class="card mb-3" id="report-section-{si}">
                    <div class="card-header">
                        <h3>{sectionConfig.title}</h3>
                    </div>
                    <div class="card-body">
                        <SurveySectionDataView
                                config={config}
                                surveyStats={surveyStats}
                                sectionIndex={si}
                                readinessDescriptions={[]}
                                useBarChart={false}>
                        </SurveySectionDataView>
                    </div>
                </div>
            {/if}
        {/each}
    {:else}
        <p>No statistics available.</p>
    {/if}
</div>
