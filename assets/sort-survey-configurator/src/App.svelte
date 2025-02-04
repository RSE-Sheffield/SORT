<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    import * as _ from 'lodash';
    import defaultConfigs from '../../../data/survey_config/sort_only_config.json';
    import SurveyConfigurator from "./lib/SurveyConfigurator.svelte";
    import SurveyResponse from "./lib/SurveyResponse.svelte";

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


    let surveyConfigComponent = $state();
    let editable = $state(true);

    let responseValue = $state();
    $inspect(responseValue);


    function validate() {
        surveyConfigComponent.validate();
    }

    function getConfig() {
        surveyConfigComponent.getConfig();
    }

    function toggleEditable() {
        editable = !editable;
    }

    function getValues() {
        surveyConfigComponent.getValue();
    }

</script>

<main>
    <div class="container">
        <div>
            <button class="btn btn-primary" onclick={validate}>Validate</button>
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
                                bind:this={surveyConfigComponent}
                                editable={editable}
            />
        {:else}
            <SurveyResponse config={configData} bind:value={responseValue}/>
        {/if}
    </div>

</main>

<style>
</style>
