<script lang="ts">
let {value = $bindable("") } = $props();
let hasFocus = $state(false);

function setFocus(focus){
    hasFocus = focus;
}


</script>

{#if hasFocus}
<textarea class="form-control" bind:value={value} onfocusout={()=> {setFocus(false)}} ></textarea>
{:else}
{value} <button class="btn btn-link " onclick={()=>{setFocus(true)}} title="Edit text" aria-label="Edit text"><i class='bx bxs-edit-alt' ></i></button>
{/if}


