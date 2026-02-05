<script lang="ts">
    interface ActiveFilter {
        label: string;
        value: string;
    }

    interface Props {
        filteredCount: number;
        totalCount: number;
        activeFilters: ActiveFilter[];
        onClearFilters: () => void;
        variant?: 'info' | 'warning';
        compact?: boolean;
    }

    let {
        filteredCount,
        totalCount,
        activeFilters,
        onClearFilters,
        variant = 'info',
        compact = false
    }: Props = $props();

    let alertClass = $derived(variant === 'info' ? 'alert-info' : 'alert-warning');
    let buttonClass = $derived(variant === 'info' ? 'btn-outline-primary' : 'btn-outline-warning');
</script>

{#if compact}
    <!-- Compact inline format for section alerts -->
    <div class="alert {alertClass} mb-3 d-flex justify-content-between align-items-center" role="alert">
        <div>
            <i class="bx bx-filter"></i>
            <strong>Filtered Data:</strong>
            Showing {filteredCount} of {totalCount} responses
            {#if activeFilters.length > 0}
                ({#each activeFilters as filter, idx (filter.label)}
                    <strong>{filter.label}:</strong> {filter.value}{idx < activeFilters.length - 1 ? ', ' : ''}
                {/each})
            {/if}
        </div>
        <button class="btn btn-sm {buttonClass} ms-3" onclick={onClearFilters}>
            <i class="bx bx-x"></i> Clear
        </button>
    </div>
{:else}
    <!-- Detailed format for main alert -->
    <div class="alert {alertClass} mb-3 d-flex justify-content-between align-items-start" role="alert">
        <div>
            <h5 class="alert-heading">
                <i class="bx bx-filter"></i> Filtered Data View
            </h5>
            <p>
                You are viewing a filtered subset of the data.
                Showing {filteredCount} of {totalCount} responses.
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
        <button class="btn btn-sm {buttonClass} ms-3" onclick={onClearFilters}>
            <i class="bx bx-x"></i> Clear Filters
        </button>
    </div>
{/if}
