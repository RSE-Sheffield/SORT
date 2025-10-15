<script lang="ts">
    import SurveyResponseComponent from "./lib/components/SurveyResponseComponent.svelte";

    let {csrf, initConfig, initResponse} = $props();

    let configData = $state(initConfig);


    //Import data from other script blocks on page (for django)
    //otherwise use the default config

    // let configData = $state(getDataInElem("configData", defaultConfigs));
    let responseValue = $state(initResponse);

</script>


<div>
    <SurveyResponseComponent config={configData} bind:value={responseValue} csrf={csrf}/>
</div>




<style>
    :global(.likert-container) {
        border-left: 4px solid #0d6efd;
        transition: all 0.3s ease;
    }

    :global(.likert-container:hover) {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px);
    }

    :global(.likert-container .card-title) {
        color: #0d6efd;
        margin-bottom: 0.5rem;
    }

    :global(.textarea-container) {
        border-left: 4px solid #198754;
        transition: all 0.3s ease;
    }

    :global(.textarea-container:hover) {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px);
    }

    :global(.textarea-container .form-label) {
        color: #198754;
        font-size: 1.1rem;
    }

    :global(.likert-container .table-light th) {
        background-color: #f8f9fa;
        border-bottom: 2px solid #dee2e6;
        position: sticky;
        top: 0;
        z-index: 10;
    }

    :global(.likert-container tbody tr:hover) {
        background-color: #f8f9fa;
    }
</style>
