<script lang="ts">
    import "quill/dist/quill.snow.css"
    import Quill from "quill/core"
    import {onMount} from "svelte";

    let {csrf, updateUrl, initContents, viewOnly=false} = $props();

    let editorRef: HTMLElement = $state();
    let quillInstance: Quill = null;
    let contents = $state();

    onMount(()=>{

        const readOnlyConfig = {
            readOnly: true,
        }
        const editorConfig = {
            theme: 'snow',
            readOnly: false,
            placeholder: "Please enter evidence for this section here...",
        }

        quillInstance = new Quill(editorRef, viewOnly ? readOnlyConfig : editorConfig);
        quillInstance.on('text-change', (delta, oldDelta, source) => {
            contents = JSON.stringify(quillInstance.getContents());
        });
        try{
            quillInstance.setContents(JSON.parse(initContents))
        } catch (e){
            //Do nothing
            console.log(e)
        }



    })
</script>
<div>
    <div bind:this={editorRef} class="mb-3"></div>
    {#if !viewOnly}
    <form
            action={updateUrl}
            method="post"
    >
        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
        <input type="hidden" name="text" bind:value={contents}/>
        <button type="submit" name="submit" class="btn btn-primary mb-3">Save statement</button>
    </form>
    {/if}
</div>
