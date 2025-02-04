<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    import * as _ from 'lodash';
    import defaultConfigs from '../../../data/survey_config/sort_only_config.json';
    import SurveyConfigurator from "./lib/SurveyConfigurator.svelte";
    import SurveyResponse from "./lib/SurveyResponse.svelte";
    import {getDataInElem} from "./lib/misc.svelte";

    //Import data from other script blocks on page (for django)
    //otherwise use the default config
    let csrf = getDataInElem("csrf", "");
    let configData = $state(getDataInElem("configData", defaultConfigs));
    let responseValue = $state();

</script>


<div>
    <SurveyResponse config={configData} bind:value={responseValue} csrf={csrf}/>
</div>




<style>
</style>
