<script lang="ts">
    import DOMPurify from "dompurify";
    import PellEditor from "./input/PellEditor.svelte";

    let {csrf, updateUrl, initContents, viewOnly = false} = $props();
    let contents = $state(initContents);


</script>
<div>
    {#if viewOnly}
        {@html DOMPurify.sanitize(contents)}
    {:else }
        <PellEditor bind:value={contents}></PellEditor>
        <form
                action={updateUrl}
                method="post"
        >
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
            <input type="hidden" name="text" bind:value={contents}/>
            <button type="submit" name="submit" class="btn btn-primary">
                <i class="bx bx-save"></i> Save statement
            </button>
        </form>
    {/if}
</div>
