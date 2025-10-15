<script lang="ts">
    import type {SurveyConfig, SurveyResponseBatch, SurveyStats} from "../interfaces.ts";
    import {generateStatsFromSurveyResponses} from "../misc.svelte.ts";
    import SurveyDemographicFilters from "./SurveyDemographicFilters.svelte";
    import CollapsibleCard from "./CollapsibleCard.svelte";
    import SortSummaryMatrix from "./SortSummaryMatrix.svelte";
    import SurveySectionDataView from "./SurveySectionDataView.svelte";
    import FilterAlert from "./FilterAlert.svelte";

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
    {/if}

    {#if config && surveyStats}
        {#if hasActiveFilters}
            <FilterAlert
                filteredCount={filteredResponses.length}
                totalCount={responses.length}
                activeFilters={activeFilters}
                onClearFilters={clearFilters}
                variant="info"
                compact={false}
            />
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
                    <FilterAlert
                        filteredCount={filteredResponses.length}
                        totalCount={responses.length}
                        activeFilters={activeFilters}
                        onClearFilters={clearFilters}
                        variant="warning"
                        compact={true}
                    />
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
