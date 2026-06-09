<script lang="ts">
  import {
    type FieldConfig,
    type SurveyConfig,
    type SurveyResponseBatch,
    TextType,
  } from "../interfaces.ts";
  import { onMount } from "svelte";

  type Range = {
    min: number;
    max: number;
  };

  type FilterItem = {
    fieldConfig: FieldConfig;
    sectionIndex: number;
    fieldIndex: number;
    valueMin?: number;
    valueMax?: number;
    options?: string[];
  };

  interface Props {
    config: SurveyConfig;
    responses: SurveyResponseBatch;
    onFilterChange?: (
      responses: SurveyResponseBatch,
      activeFilters?: Array<{
        label: string;
        value: string;
      }>,
    ) => void;
    onClearFiltersCallback?: (clearCallback: () => void) => void;
  }

  let { config, responses, onFilterChange, onClearFiltersCallback }: Props =
    $props();
  let filterItems: FilterItem[] = $state([]);
  // Categorical filters hold an array of selected options (empty = "All").
  // Numeric (text) filters hold a {min, max} Range.
  let filterValues: (string[] | Range | null)[] = $state([]);
  let filteredResponses = $state(responses);
  let initialFilterValues: Array<null | Range | string[]> = [];

  onMount(() => {
    for (let si = 0; si < config.sections.length; si++) {
      if (config.sections[si].type === "demographic") {
        for (let fi = 0; fi < config.sections[si].fields.length; fi++) {
          const fieldConfig = config.sections[si].fields[fi];
          // Hide deactivated fields
          if (fieldConfig.disabled) {
            console.log(`Concealing disabled field "${fieldConfig.label}"`);
            continue;
          }
          switch (fieldConfig.type) {
            case "checkbox":
            case "select":
            case "radio":
              {
                const filterOptions = fieldConfig.hasOtherOption
                  ? getAllOptionsFromField(fieldConfig, responses, si, fi)
                  : fieldConfig.options;
                filterItems.push({
                  fieldConfig: fieldConfig,
                  sectionIndex: si,
                  fieldIndex: fi,
                  options: filterOptions,
                });
                filterValues.push([]);
                initialFilterValues.push([]);
              }
              break;
            case "text":
              if (
                fieldConfig.textType === TextType.decimals ||
                fieldConfig.textType === TextType.integer
              ) {
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
                const initialRange: Range = { min: min, max: max };
                filterValues.push({ ...initialRange });
                initialFilterValues.push({ ...initialRange });
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
    const activeFilters: Array<{ label: string; value: string }> = [];

    for (let ri = 0; ri < responses.length; ri++) {
      let addToFilteredSet = true;
      for (
        let filterIndex = 0;
        filterIndex < filterItems.length;
        filterIndex++
      ) {
        const filterItem = filterItems[filterIndex];
        const filterValue = filterValues[filterIndex];
        if (filterItem.fieldConfig.type === "text") {
          const value = Number(
            responses[ri][filterItem.sectionIndex][filterItem.fieldIndex],
          );
          if (!(value >= filterValue.min && value <= filterValue.max)) {
            addToFilteredSet = false;
            break;
          }
        } else {
          // Categorical filter: keep the response if its value is one of the
          // selected options. An empty selection means "All" (no filtering).
          if (
            Array.isArray(filterValue) &&
            filterValue.length > 0 &&
            !filterValue.includes(
              responses[ri][filterItem.sectionIndex][filterItem.fieldIndex],
            )
          ) {
            addToFilteredSet = false;
            break;
          }
        }
      }
      if (addToFilteredSet) {
        filteredResponses.push(responses[ri]);
      }
    }

    // Build list of active filters for display
    for (let filterIndex = 0; filterIndex < filterItems.length; filterIndex++) {
      const filterItem = filterItems[filterIndex];
      const filterValue = filterValues[filterIndex];

      if (filterItem.fieldConfig.type === "text" && isRange(filterValue)) {
        // Check if range filter differs from full range
        if (
          filterValue.min !== filterItem.valueMin ||
          filterValue.max !== filterItem.valueMax
        ) {
          activeFilters.push({
            label: filterItem.fieldConfig.label,
            value: `${filterValue.min} to ${filterValue.max}`,
          });
        }
      } else {
        // Check if categorical filter has any selected options
        if (Array.isArray(filterValue) && filterValue.length > 0) {
          activeFilters.push({
            label: filterItem.fieldConfig.label,
            value: filterValue.join(", "),
          });
        }
      }
    }

    onFilterChange?.(filteredResponses, activeFilters);
  }

  function clearFilters() {
    // Reset all filter values to their initial state
    for (let i = 0; i < filterValues.length; i++) {
      const initial = initialFilterValues[i];
      if (Array.isArray(initial)) {
        // Categorical filter - fresh empty array copy
        filterValues[i] = [...initial];
      } else if (typeof initial === "object" && initial !== null) {
        // Range filter - deep copy
        filterValues[i] = { ...initial };
      } else {
        filterValues[i] = initial;
      }
    }
    // Trigger filter change with reset values
    handleFilterChange();
  }

  function toggleOption(index: number, option: string, checked: boolean) {
    const current = filterValues[index];
    const selected = Array.isArray(current) ? current : [];
    // Reassign (don't mutate in place) so Svelte runes reactivity fires.
    filterValues[index] = checked
      ? [...selected, option]
      : selected.filter((o) => o !== option);
    handleFilterChange();
  }

  function isRange(value: unknown): value is Range {
    return (
      value !== null &&
      typeof value === "object" &&
      "min" in value &&
      "max" in value
    );
  }

  function getAllOptionsFromField(
    fieldConfig: FieldConfig,
    responses: SurveyResponseBatch,
    sectionIndex: number,
    fieldIndex: number,
  ) {
    const allOptions = new Set<string>(fieldConfig.options);
    for (const response of responses) {
      allOptions.add(response[sectionIndex][fieldIndex]);
    }
    return [...allOptions];
  }
</script>

{#if filterItems && filterValues}
  {#each filterItems as fItem, fItemIndex (fItemIndex)}
    {#if fItem.fieldConfig.type === "text"}
      <strong>{fItem.fieldConfig.label}</strong>
      <div class="row">
        <div class="col">
          <label class="form-label">
            Minimum
            <input
              type="range"
              class="form-range"
              min={fItem.valueMin}
              max={filterValues[fItemIndex].max}
              bind:value={filterValues[fItemIndex].min}
              onchange={handleFilterChange}
            />
            <input
              class="form-control"
              min={fItem.valueMin}
              max={fItem.valueMax}
              bind:value={filterValues[fItemIndex].min}
            />
          </label>
        </div>
        <div class="col">
          <label class="form-label">
            Maximum
            <input
              type="range"
              class="form-range"
              min={filterValues[fItemIndex].min}
              max={fItem.valueMax}
              bind:value={filterValues[fItemIndex].max}
              onchange={handleFilterChange}
            />
            <input
              class="form-control"
              min={fItem.valueMin}
              max={fItem.valueMax}
              bind:value={filterValues[fItemIndex].max}
            />
          </label>
        </div>
      </div>
    {:else}
      <fieldset class="mb-3">
        <legend class="form-label h6"
          ><strong>{fItem.fieldConfig.label}</strong></legend
        >
        {#each fItem.options as option}
          <div class="form-check">
            <input
              class="form-check-input"
              type="checkbox"
              id="filter-{fItemIndex}-{option}"
              value={option}
              checked={filterValues[fItemIndex].includes(option)}
              onchange={(e) =>
                toggleOption(fItemIndex, option, e.currentTarget.checked)}
            />
            <label class="form-check-label" for="filter-{fItemIndex}-{option}"
              >{option}</label
            >
          </div>
        {/each}
      </fieldset>
    {/if}
  {/each}

  <div>
    <h5>Showing {filteredResponses.length} responses.</h5>
  </div>
{/if}
