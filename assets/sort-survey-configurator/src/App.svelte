<svelte:options customElement="survey-configurator" />
<script lang="ts">
  import _ from 'lodash/lodash'
  import testConfigs from './assets/test_configs'
  import SurveyConfigurator from "./lib/SurveyConfigurator.svelte";

  //Test importing data from other script blocks on page (for django)
  let data = JSON.parse(document.getElementById("programData").textContent);

  //Import test config data from json file
  let configData = $state(_.cloneDeep(testConfigs));
  console.log(data);
</script>

<main>
  <div class="container">
    <SurveyConfigurator bind:surveyConfig={configData}></SurveyConfigurator>
  </div>

</main>

<style>
</style>
