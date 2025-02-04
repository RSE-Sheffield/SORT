<script lang="ts">
    let {options = $bindable(), type = ""} = $props();

    function addOption(){
        options.push("Option " + (options.length + 1));
    }

    function deleteOption(index){
        options.splice(index, 1);
    }
</script>
{#each options as option, index}
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
     <input class="form-control" type="text" bind:value={options[index]} />
    <button class="btn btn-outline-danger" onclick={()=>{deleteOption(index)}}><i class='bx bx-x' ></i></button>
</div>
{/each}
<div>
    <button class="btn btn-primary btn-sm" onclick={addOption}>Add option</button>
</div>
