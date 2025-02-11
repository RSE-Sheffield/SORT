<script lang="ts">
    import * as _ from "lodash"
    import SectionComponent from "./input/SectionComponent.svelte";

    let {
        config = $bindable(),
        value = $bindable(),
        initValue = null,
        csrf = "",
    } = $props();

    $inspect(value);

    let isValid = $state();    let isInvalid = $state();

    function setIsValid(valid) {
        isValid = valid;
        isInvalid = !valid;
    }

    function clearValidation(){
        isValid = false;
        isInvalid = false;
    }

    // Keeps track of all section components
    // when components are deleted the derived property filters this out
    let currentSectionComponent = $state();

    // Value in plaintext for submitting to the backend
    let valueStr = $derived(JSON.stringify(value))


    let sectionValues = $state(initValue !== null ? initValue : []);
    $effect(() => {
        value = sectionValues;
    })

    let currentPage = $state(0);

    function validate() {
        const currentPageValidates = currentSectionComponent.validate();
        setIsValid(currentPageValidates)
        return currentPageValidates;
    }

    function previousPage() {
        if (currentPage > 0) {
            currentPage -= 1;
            clearValidation();
        }
    }

    function nextPage() {
        if (validate()) {
            if (currentPage < config.sections.length - 1) {
                currentPage += 1;
                clearValidation();
            }
        }
    }

    function onSubmitHandler(e) {
        if (!validate()) {
            // Don't submit if there's still an error on the page
            e.preventDefault();
        }
    }


</script>
{#each config.sections as section, index (index)}
    {#if currentPage === index}
        <SectionComponent bind:config={config.sections[index]}
                          editable={false}
                          displaySectionType={false}
                          bind:value={sectionValues[index]}
                          bind:this={currentSectionComponent}
        />
    {/if}
{/each}
{#if isInvalid}
<div class="alert alert-danger mb-3">
    Values are incorrect or missing. Please check the values above before continuing.
</div>
{/if}

<div class="row">
    <div class="col-1">
        <button class="btn btn-primary" disabled={currentPage < 1} onclick={previousPage}>Previous</button>
    </div>
    <div class="col-1">
        {#if currentPage < config.sections.length - 1}
            <button class="btn btn-primary" onclick={nextPage}>Next</button>
        {:else}
            <form method="post" onsubmit={onSubmitHandler}>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
                <input type="hidden" name="value" value="{valueStr}"/>
                <input type="submit" class="btn btn-primary" value="Submit"/>
            </form>
        {/if}
    </div>
</div>
