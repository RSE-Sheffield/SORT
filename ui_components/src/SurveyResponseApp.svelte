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

    /* Enhanced radio button styling for Likert scales */
    :global(.likert-radio-input) {
        width: 1.5rem !important;
        height: 1.5rem !important;
        cursor: pointer;
        margin: 0;
    }

    :global(.likert-radio-input:hover) {
        transform: scale(1.1);
        transition: transform 0.2s ease;
    }

    :global(.likert-radio-label) {
        display: inline-block;
        padding: 0.75rem;
        cursor: pointer;
        margin: 0;
        width: 100%;
        height: 100%;
    }

    :global(.likert-radio-label:hover) {
        background-color: rgba(13, 110, 253, 0.1);
        border-radius: 0.25rem;
    }

    /* Mobile Likert item styling */
    :global(.likert-mobile-label) {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        cursor: pointer;
        border-radius: 0.25rem;
        transition: background-color 0.2s ease;
    }

    :global(.likert-mobile-label:hover) {
        background-color: rgba(13, 110, 253, 0.1);
    }

    /* Make table cells with radio buttons easier to click */
    :global(.likert-container td.text-center) {
        padding: 0 !important;
        vertical-align: middle;
    }

    /* Checked state visual feedback */
    :global(.likert-radio-input:checked) {
        background-color: #0d6efd;
        border-color: #0d6efd;
        box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
    }

    :global(.likert-radio-label:has(input:checked)) {
        background-color: rgba(13, 110, 253, 0.15);
    }

    :global(.likert-mobile-label:has(input:checked)) {
        background-color: rgba(13, 110, 253, 0.15);
        font-weight: 600;
    }
</style>
