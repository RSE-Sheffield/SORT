<script lang="ts">
    import {type FileDescriptionType} from "../interfaces.ts";
    import axios from "axios";


    interface FileBrowserItemProps {
        file: FileDescriptionType,
        csrf: string
    }

    let {file, csrf}: FileBrowserItemProps = $props();

    let previewEnabled = $state(false);
    let fileContent = $state(null);


    async function getFileContents() {
        const response = await axios.get(file.fileUrl);
        if (response.status == 200) {
            fileContent = response.data;
        }
    }

    let textExtensions = [".txt"];

    let fetchExtensions = [...textExtensions];
    let pdfExtension = [".pdf"];
    let imgExtensions = [".jpg", ".jpg", ".png", ".svg"]
    let supportedExtensions = [...fetchExtensions, ...pdfExtension, ...imgExtensions]

    function stringContainsExtension(str: string, extensionList: string[]) {
        return extensionList.some(extension => str.toLowerCase().endsWith(extension))
    }

    function handlePreviewToggle() {
        previewEnabled = !previewEnabled;
        if (fileContent == null && fetchExtensions.some(extension => file.name.toLowerCase().endsWith(extension))) {
            getFileContents();
        }
    }


</script>

<div class="d-flex justify-content-between">
    <a href={file.fileUrl} class="flex-fill">{file.name}</a>
    <div></div>
    <div class="flex-fill d-flex justify-content-end">
        {#if stringContainsExtension(file.name, supportedExtensions)}
        <button
                class="btn btn-primary me-3"
                onclick={handlePreviewToggle}
                >
            {#if previewEnabled}
                <i class='bx bxs-hide' ></i> Close preview
            {:else }
                <i class='bx bxs-show' ></i> Preview
            {/if}
        </button>
        {:else}
            <button class="btn btn-primary me-3" disabled title="Preview for this file is not available, please download it">
            <i class='bx bxs-hide' ></i> No preview
        </button>
        {/if}

        <a href={file.fileUrl} class="btn btn-primary me-3">
            <i class='bx bx-cloud-download'></i> Download</a>
        <form action={file.deleteUrl} method="post">
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
            <button type="submit" class="btn btn-danger"><i class="bx bxs-trash"></i> Delete</button>
        </form>
    </div>
</div>
{#if previewEnabled}
    <div class="p-3">
        {#if stringContainsExtension(file.name, imgExtensions)}
            <img src={file.fileUrl} style="width:100%; height: 100%"/>
        {:else if stringContainsExtension(file.name, pdfExtension)}
            <embed src={file.fileUrl} style="width: 100%; height: auto; min-height: 50em" />
        {:else if stringContainsExtension(file.name, fetchExtensions)}
            {fileContent}
        {:else}
            Unsupported file type, please download to view
        {/if}
    </div>
{/if}

