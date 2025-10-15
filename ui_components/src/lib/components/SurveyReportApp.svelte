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
    }

    interface ActiveFilter {
        label: string;
        value: string;
    }

    let {config, responses}: SurveyReportAppProps = $props();
    let filteredResponses = $state(responses);
    let activeFilters = $state<ActiveFilter[]>([]);
    let clearFiltersCallback = $state<(() => void) | null>(null);

    // Calculate section stats based on filtered responses
    let surveyStats: SurveyStats | null = $derived.by(() => {
        if (config === null ||
            responses === null ||
            responses === undefined ||
            responses.length < 1)
            return null;

        return generateStatsFromSurveyResponses(config, filteredResponses);
    });

    // Check if any filters are active
    let hasActiveFilters = $derived(filteredResponses.length < responses.length || activeFilters.length > 0);

    function handleFilterChange(changedFilteredResponses: SurveyResponseBatch, filters?: ActiveFilter[]) {
        filteredResponses = changedFilteredResponses;
        if (filters) {
            activeFilters = filters;
        }
    }

    function handleClearFiltersCallback(callback: () => void) {
        clearFiltersCallback = callback;
    }

    function clearFilters() {
        if (clearFiltersCallback) {
            clearFiltersCallback();
        }
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
                        onClearFiltersCallback={handleClearFiltersCallback}
                />
            {/snippet}
        </CollapsibleCard>

        <div class="mb-3 d-flex justify-content-between align-items-center">
            <strong>Responses shown: {filteredResponses.length} of {responses.length}</strong>
        </div>
    {/if}

    {#if config && surveyStats}
        {#if hasActiveFilters}
            <div class="alert alert-info mb-3 d-flex justify-content-between align-items-start" role="alert">
                <div>
                    <h5 class="alert-heading">
                        <i class="bx bx-filter"></i> Filtered Data View
                    </h5>
                    <p>
                        You are viewing a filtered subset of the data.
                        Showing {filteredResponses.length} of {responses.length} responses.
                    </p>
                    {#if activeFilters.length > 0}
                        <hr>
                        <p class="mb-1"><strong>Active filters:</strong></p>
                        <ul class="mb-0">
                            {#each activeFilters as filter (filter.label)}
                                <li><strong>{filter.label}:</strong> {filter.value}</li>
                            {/each}
                        </ul>
                    {/if}
                </div>
                <button class="btn btn-sm btn-outline-primary ms-3" onclick={clearFilters}>
                    <i class="bx bx-x"></i> Clear Filters
                </button>
            </div>
        {/if}

        <div class="card mb-3">
            <div class="card-header"><h3>Summary Ranking Matrix</h3></div>
            <div class="card-body">
                <p>Summary of survey participant's overall average perception for each section.</p>
                <SortSummaryMatrix config={config} surveyStats={surveyStats}></SortSummaryMatrix>
            </div>
        </div>

        {#each config.sections as sectionConfig, si (si)}
            {#if sectionConfig.type !== "consent"}
                {#if hasActiveFilters}
                    <div class="alert alert-warning mb-3 d-flex justify-content-between align-items-center" role="alert">
                        <div>
                            <i class="bx bx-filter"></i>
                            <strong>Filtered Data:</strong>
                            Showing {filteredResponses.length} of {responses.length} responses
                            {#if activeFilters.length > 0}
                                ({#each activeFilters as filter, idx (filter.label)}
                                    <strong>{filter.label}:</strong> {filter.value}{idx < activeFilters.length - 1 ? ', ' : ''}
                                {/each})
                            {/if}
                        </div>
                        <button class="btn btn-sm btn-outline-warning ms-3" onclick={clearFilters}>
                            <i class="bx bx-x"></i> Clear
                        </button>
                    </div>
                {/if}
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
