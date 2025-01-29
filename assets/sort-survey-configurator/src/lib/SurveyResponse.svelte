<script lang="ts">
    import * as _ from "lodash"
    import SectionComponent from "./input/SectionComponent.svelte";
    let {
        config = $bindable(),
        value = $bindable(),
        initValue = null,
        csrf = "",
    } = $props();

    // Value in plaintext for submitting to the backend
    let valueStr = $derived(JSON.stringify(value))


    let sectionValues = $state(initValue !== null ? initValue : []);
    $effect(()=>{
        value = sectionValues;
    })

    let currentPage = $state(0);

    function previousPage(){
        if(currentPage > 0){
            currentPage -= 1;
        }
    }

    function nextPage(){
        if(currentPage < config.sections.length - 1){
            currentPage += 1;
        }
    }




</script>
{#each config.sections as section, index (index)}
    {#if currentPage === index}
    <SectionComponent bind:config={config.sections[index]}
                      editable={false}
                      displaySectionType={false}
                      bind:value={sectionValues[index]}
    />
    {/if}
{/each}
<div class="row">
    <div class="col-1">
        <button class="btn btn-primary" disabled={currentPage < 1} onclick={previousPage}>Previous</button>
    </div>
    <div class="col-1">
        {#if currentPage < config.sections.length - 1}
        <button class="btn btn-primary" onclick={nextPage}>Next</button>
        {:else}
        <form method="post">
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
            <input type="hidden" name="value" value="{valueStr}"/>
            <input type="submit" class="btn btn-primary" value="Submit"/>
        </form>
        {/if}
    </div>
</div>
