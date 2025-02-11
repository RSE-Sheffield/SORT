<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    /**
     * Harness for testing SORT UI components
     */
    import * as _ from 'lodash';
    import defaultConfigs from '../../../data/survey_config/all_elements_test_config.json';
    import SurveyConfigurator from "./lib/components/SurveyConfigurator.svelte";
    import SurveyResponse from "./lib/components/SurveyResponse.svelte";
    import {download} from "./lib/misc.svelte.js";

    //Import data from other script blocks on page (for django)
    //otherwise use the default config
    let elem = document.getElementById("configData");
    let initConfigData = {};
    if(elem){
        initConfigData = JSON.parse(elem.textContent);
    }
    else{
        initConfigData = defaultConfigs;
    }
    let configData = $state(_.cloneDeep(initConfigData));


    let surveyComponent = $state();
    let editable = $state(true);

    let responseValue = $state();




    function getConfig() {
        download("config.json", JSON.stringify(configData, null, 2))
    }

    function toggleEditable() {
        editable = !editable;
    }

    function getValues() {
        download("values.json", JSON.stringify(responseValue, null, 2))
    }

</script>
<nav class="navbar navbar-expand-lg bg-body-tertiary mb-3">
    <div class="container-fluid">
        <h2>SORT UI Dev test page</h2>
    </div>
</nav>
<main>
    <div class="container">
        <div class="btn-group mb-3" role="group" aria-label="Test functions">
            <button class="btn btn-primary" onclick={getConfig}>Get config</button>
            <button class="btn btn-primary" onclick={toggleEditable}>
                {#if editable}
                    Turn off editing
                {:else}
                    Turn on editing
                {/if}
            </button>
            <button class="btn btn-primary" onclick={getValues}>Get values</button>
        </div>

        {#if editable}
            <SurveyConfigurator bind:config={configData}
                                bind:this={surveyComponent}
                                editable={editable}
            />
        {:else}
            <SurveyResponse config={configData} bind:value={responseValue} bind:this={surveyComponent}/>
        {/if}
    </div>

</main>

<style>
</style>
