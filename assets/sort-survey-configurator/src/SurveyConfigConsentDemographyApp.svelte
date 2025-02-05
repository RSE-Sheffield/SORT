<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    import * as _ from 'lodash';
    import defaultConsentConfigs from '../../../data/survey_config/consent_only_config.json';
    import defaultDemographicConfigs from '../../../data/survey_config/demography_only_config.json';
    import SurveyConfigurator from "./lib/SurveyConfigurator.svelte";
    import {getDataInElem} from "./lib/misc.svelte";

    //Import data from other script blocks on page (for django)
    //otherwise use the default config

    let csrf = getDataInElem("csrf", "");
    let consentConfig = $state(getDataInElem("consentConfig", defaultConsentConfigs));
    let demographyConfig = $state(getDataInElem("demographyConfig", defaultDemographicConfigs));

    let consentConfigStr = $derived(JSON.stringify(consentConfig))
    let demographyConfigStr = $derived(JSON.stringify(demographyConfig))

    $inspect(consentConfig);
    $inspect(demographyConfig);
</script>


<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your welcome and consent page</h2>
        <p></p>

        <SurveyConfigurator bind:config={consentConfig}
                            sectionTypeEditable={false}
                            sectionEditable={false}
        />
    </div>

</div>
<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your demographys page</h2>
        <p></p>
        <SurveyConfigurator bind:config={demographyConfig}
                            sectionTypeEditable={false}
                            sectionEditable={false}
        />
    </div>
</div>

<form method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
    <input type="hidden" name="consent_config" value="{consentConfigStr}"/>
    <input type="hidden" name="demography_config" value="{demographyConfigStr}"/>
    <input type="submit" class="btn btn-primary" value="Submit"/>
</form>


<style>
</style>
