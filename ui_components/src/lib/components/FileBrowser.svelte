<script lang="ts">
    import {type FileDescriptionType} from "../interfaces.ts";
    import FileBrowserItem from "./FileBrowserItem.svelte";


    interface FileBrowserProps {
        filesList: FileDescriptionType[]
        csrf: string
    }

    let {filesList, csrf}: FileBrowserProps = $props()
</script>
<div>
    <ul class="list-group">
        {#each filesList as file (file.name)}
            <li class="list-group-item">
                <FileBrowserItem file={file} csrf={csrf}></FileBrowserItem>
            </li>
        {/each}
    </ul>
</div>
