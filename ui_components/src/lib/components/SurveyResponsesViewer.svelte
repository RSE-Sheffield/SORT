<script lang="ts">
    import SurveyResponseViewer from "./SurveyResponseViewer.svelte";

    let {config, responses} = $props();
    let currentIndex: number = $state(0);
</script>
<div>
    <div class="card mb-3">
        <div class="card-body">
            <p>Click response entries below to view individual responses.</p>

            <div class="d-flex flex-wrap m-2">
                {#each responses as response, index}
                    <button class={{"m-1": true, "btn":true, "btn-primary": currentIndex===index, "btn-secondary": currentIndex !==index}}
                            onclick={()=>{currentIndex = index}}
                            aria-label={"Response entry "+(index+1)}
                    >
                        {index + 1}
                    </button>
                {/each}
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <h3>Survey response {currentIndex+1}</h3>
        </div>
        <div class="card-body">
            {#if responses !== null && responses !== undefined && responses.length > 0}
                {#key currentIndex}
                    <SurveyResponseViewer config={config} response={responses[currentIndex]}/>
                {/key}
            {:else }

                <p>
                    No responses
                </p>

            {/if}
        </div>
    </div>
</div>
