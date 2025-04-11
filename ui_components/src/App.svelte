<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    /**
     * Harness for testing SORT UI components
     */
    import * as _ from "lodash-es";
    import defaultConfigs from '../../../data/survey_config/all_elements_test_config.json';
    import SurveyConfigurator from "./lib/components/SurveyConfigurator.svelte";
    import SurveyResponseComponent from "./lib/components/SurveyResponseComponent.svelte";
    import {download} from "./lib/misc.svelte.js";
    import SurveyConfigConsentDemographyApp from "./SurveyConfigConsentDemographyApp.svelte";

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


    let page = $state(0);

</script>
<nav class="navbar navbar-expand-lg bg-body-tertiary mb-3">
    <div class="container-fluid">
        <h2>SORT UI Dev test page</h2>
    </div>
    <div class="collapse navbar-collapse">
        <ul class="navbar-nav">
            <li class="nav-item">
                <a class="nav-link" href="/" onclick={(e)=> {e.preventDefault(); e.stopPropagation(); page = 0;}}>Main</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/" onclick={(e)=>{e.preventDefault(); e.stopPropagation(); page = 1;}}>Consent demography</a>
            </li>
        </ul>
    </div>
</nav>
<main>
    {#if page == 0}
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
            <SurveyResponseComponent config={configData} bind:value={responseValue} bind:this={surveyComponent}/>
        {/if}
    </div>
    {:else if page == 1}

    <div class="container">
        <SurveyConfigConsentDemographyApp></SurveyConfigConsentDemographyApp>
    </div>
    {/if}

</main>

<style>
</style>
