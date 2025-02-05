<script lang="ts">
let {value = $bindable("") } = $props();
let hasFocus = $state(false);

function setFocus(focus){
    hasFocus = focus;
}

function init(el){
    el.focus();
}

</script>

{#if hasFocus}
<input class="form-control" bind:value={value} onfocusout={()=> {setFocus(false)}} use:init/>
{:else}
{value} <button class="btn btn-link " onclick={()=>{setFocus(true)}} title="Edit text"><i class='bx bxs-edit-alt' ></i></button>
{/if}


