<script lang="ts">
    let {options = $bindable(), type = "", readonly=false} = $props();

    function addOption(){
        options.push("Option " + (options.length + 1));
    }

    function deleteOption(index){
        options.splice(index, 1);
    }
</script>
{#each options as option, index (index)}
<div class="input-group mb-1">
     <span class="input-group-text">
         {#if type === "radio"}
            <i class='bx bx-radio-circle-marked' ></i>
         {:else if type === "checkbox"}
             <i class='bx bx-check-square' ></i>
         {:else if type === "select"}
             <i class='bx bx-menu' ></i>
         {:else if type === "likert"}
             <i class='bx bxs-grid'></i>
         {/if}
     </span>
     <input class="form-control" type="text" bind:value={options[index]} readonly={readonly}/>
    {#if readonly}
    <button class="btn btn-outline-secondary" aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {:else}
    <button class="btn btn-outline-danger" onclick={()=>{deleteOption(index)}} aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {/if}
</div>
{/each}
<div>
    {#if readonly}
    <button class="btn btn-secondary btn-sm"><i class="bx bx-plus"></i> Add option</button>
    {:else}
    <button class="btn btn-primary btn-sm" onclick={addOption}><i class="bx bx-plus"></i> Add option</button>
    {/if}
</div>
