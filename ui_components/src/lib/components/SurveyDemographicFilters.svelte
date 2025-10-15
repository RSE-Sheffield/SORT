<script lang="ts">

    import {type FieldConfig, type SurveyConfig, type SurveyResponseBatch, TextType} from "../interfaces.ts";
    import {onMount} from "svelte";

    type FilterItem = {
        fieldConfig: FieldConfig;
        sectionIndex: number;
        fieldIndex: number;
        valueMin?: number;
        valueMax?: number;
    }

    interface Props {
        config: SurveyConfig;
        responses: SurveyResponseBatch;
        onFilterChange?: (responses: SurveyResponseBatch, activeFilters?: Array<{label: string, value: string}>) => void;
        onClearFiltersCallback?: (clearCallback: () => void) => void;
    }

    let {config, responses, onFilterChange, onClearFiltersCallback}: Props = $props();
    let filterItems: FilterItem[] = $state([]);
    let filterValues = $state([]);
    let filteredResponses = $state(responses);
    let initialFilterValues: any[] = [];

    onMount(() => {
        for (let si = 0; si < config.sections.length; si++) {
            if (config.sections[si].type === "demographic") {
                for (let fi = 0; fi < config.sections[si].fields.length; fi++) {
                    const fieldConfig = config.sections[si].fields[fi];
                    // Hide deactivated fields
                    if (fieldConfig.disabled) {
                        console.log(`Concealing disabled field "${fieldConfig.label}"`);
                        break;
                    }
                    switch (fieldConfig.type) {
                        case "checkbox":
                        case "select":
                        case "radio":
                            filterItems.push({
                                fieldConfig: fieldConfig,
                                sectionIndex: si,
                                fieldIndex: fi,
                            });
                            filterValues.push(null);
                            initialFilterValues.push(null);
                            break;
                        case "text":
                            if (fieldConfig.textType === TextType.decimals ||
                                fieldConfig.textType === TextType.integer) {
                                let min = 0;
                                let max = 0;
                                for (let ri = 0; ri < responses.length; ri++) {
                                    const value = Number(responses[ri][si][fi]);
                                    if (min >= value) min = value;
                                    if (max <= value) max = value;
                                }
                                filterItems.push({
                                    fieldConfig: fieldConfig,
                                    sectionIndex: si,
                                    fieldIndex: fi,
                                    valueMax: max,
                                    valueMin: min,
                                });
                                const initialRange = {min: min, max: max};
                                filterValues.push({...initialRange});
                                initialFilterValues.push({...initialRange});
                            }
                            break;

                    }

                }
            }
        }

        // Provide clear filters callback to parent
        if (onClearFiltersCallback) {
            onClearFiltersCallback(clearFilters);
        }
    });

    function handleFilterChange() {
        filteredResponses = [];
        const activeFilters: Array<{label: string, value: string}> = [];

        for (let ri = 0; ri < responses.length; ri++) {
            let addToFilteredSet = true;
            for (let filterIndex = 0; filterIndex < filterItems.length; filterIndex++) {
                const filterItem = filterItems[filterIndex];
                const filterValue = filterValues[filterIndex];
                if (filterItem.fieldConfig.type === "text") {
                    const value = Number(responses[ri][filterItem.sectionIndex][filterItem.fieldIndex]);
                    if (!(value >= filterValue.min && value <= filterValue.max)) {
                        addToFilteredSet = false;
                        break;
                    }
                } else {
                    if (filterValue !== null &&
                        responses[ri][filterItem.sectionIndex][filterItem.fieldIndex] !== filterValue) {
                        addToFilteredSet = false;
                        break;
                    }
                }

            }
            if (addToFilteredSet) {
                filteredResponses.push(responses[ri])
            }
        }

        // Build list of active filters for display
        for (let filterIndex = 0; filterIndex < filterItems.length; filterIndex++) {
            const filterItem = filterItems[filterIndex];
            const filterValue = filterValues[filterIndex];

            if (filterItem.fieldConfig.type === "text") {
                // Check if range filter differs from full range
                if (filterValue.min !== filterItem.valueMin || filterValue.max !== filterItem.valueMax) {
                    activeFilters.push({
                        label: filterItem.fieldConfig.label,
                        value: `${filterValue.min} to ${filterValue.max}`
                    });
                }
            } else {
                // Check if categorical filter is set
                if (filterValue !== null) {
                    activeFilters.push({
                        label: filterItem.fieldConfig.label,
                        value: filterValue
                    });
                }
            }
        }

        onFilterChange?.(filteredResponses, activeFilters);
    }

    function clearFilters() {
        // Reset all filter values to their initial state
        for (let i = 0; i < filterValues.length; i++) {
            if (typeof initialFilterValues[i] === 'object' && initialFilterValues[i] !== null) {
                // Range filter - deep copy
                filterValues[i] = {...initialFilterValues[i]};
            } else {
                // Categorical filter
                filterValues[i] = initialFilterValues[i];
            }
        }
        // Trigger filter change with reset values
        handleFilterChange();
    }

</script>
{#if filterItems && filterValues}
    {#each filterItems as fItem, fItemIndex (fItemIndex)}
        {#if fItem.fieldConfig.type === "text" }

            <strong>{fItem.fieldConfig.label}</strong>
            <div class="row">
                <div class="col">
                    <label class="form-label">
                        Min
                        <input type="range" class="form-range" min={fItem.valueMin} max={filterValues[fItemIndex].max}
                               bind:value={filterValues[fItemIndex].min} onchange={handleFilterChange}>
                        <input class="form-control" min={fItem.valueMin} max={fItem.valueMax}
                               bind:value={filterValues[fItemIndex].min}>
                    </label>

                </div>
                <div class="col">
                    <label class="form-label">
                        Max
                        <input type="range" class="form-range" min={filterValues[fItemIndex].min} max={fItem.valueMax}
                               bind:value={filterValues[fItemIndex].max} onchange={handleFilterChange}>
                        <input class="form-control" min={fItem.valueMin} max={fItem.valueMax}
                               bind:value={filterValues[fItemIndex].max}>
                    </label>
                </div>

            </div>


        {:else}
            <label class="form-label">
                <strong>{fItem.fieldConfig.label}</strong>
                <select class="form-select" bind:value={filterValues[fItemIndex]} onchange={handleFilterChange}>
                    <option value={null}>All</option>
                    {#each fItem.fieldConfig.options as option}
                        <option value={option}>{option}</option>
                    {/each}
                </select>
            </label>
        {/if}
    {/each}

    <div>
        <h5>Showing {filteredResponses.length} responses.</h5>
    </div>
{/if}
