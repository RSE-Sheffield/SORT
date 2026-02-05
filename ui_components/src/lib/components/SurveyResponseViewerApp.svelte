<script lang="ts">

    import SurveyResponsesViewer from "./SurveyResponsesViewer.svelte";
    import type {SurveyConfig, SurveyResponseBatch} from "../interfaces.ts";
    import SurveyDataView from "./SurveyDataView.svelte";

    interface Props {
        config: SurveyConfig | null;
        responses: SurveyResponseBatch | null;
        csvDownloadUrl: string;
    }
    let {config, responses, csvDownloadUrl}: Props = $props();
    let currentPage = $state(0);





</script>
<div>
    <h1><i class='bx bxs-data'></i> Collected responses</h1>

    <div class="card mb-3">
        <div class="card-body">

            <div class="mb-3">
                <strong>Responses collected:</strong> { responses.length }
            </div>
            <div>
                <a href={csvDownloadUrl} class="btn btn-primary" download
                title="Download the responses in comma-separated values format">
                    <i class="bx bx-export"></i>&nbsp;Export survey data as CSV</a>
            </div>

        </div>
    </div>

    <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
            <a class={{"nav-link": true, "active": currentPage === 0}}
               href="#" onclick={(e)=>{e.preventDefault(); currentPage = 0;}}>
                Data viewer
            </a>

        </li>

        <li class="nav-item">
            <a class={{"nav-link": true, "active": currentPage === 1}}
               href="#" onclick={(e)=>{e.preventDefault(); currentPage = 1;}}>
                Result viewer
            </a>
        </li>
    </ul>

    {#if currentPage === 0}
        <!-- Summary analytics -->
        <SurveyDataView config={config} responses={responses}></SurveyDataView>
    {/if}

    {#if currentPage === 1}
        <!-- Individual form submissions -->
        <SurveyResponsesViewer config={config} responses={responses}/>
    {/if}

</div>
