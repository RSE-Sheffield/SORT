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
</style>
