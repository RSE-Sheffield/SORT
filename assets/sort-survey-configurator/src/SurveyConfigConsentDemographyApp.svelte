<svelte:options customElement="survey-configurator"/>
<script lang="ts">
    import * as _ from 'lodash';
    import defaultConsentConfigs from '../../../data/survey_config/consent_only_config.json';
    import defaultDemographicConfigs from '../../../data/survey_config/demography_only_config.json';
    import SurveyConfigurator from "./lib/components/SurveyConfigurator.svelte";
    import {getDataInElem} from "./lib/misc.svelte.js";

    //Import data from other script blocks on page (for django)
    //otherwise use the default config

    let csrf = getDataInElem("csrf", "");
    let consentConfig = $state(getDataInElem("consentConfig", defaultConsentConfigs));
    let demographyConfig = $state(getDataInElem("demographyConfig", defaultDemographicConfigs));

    let consentConfigStr = $derived(JSON.stringify(consentConfig))
    let demographyConfigStr = $derived(JSON.stringify(demographyConfig))
</script>


<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your welcome and consent page</h2>
        <p>
            The introduction page of your survey page can be configured below. We've provided a default consent page which
            can be freely customised.
        </p>

        <SurveyConfigurator bind:config={consentConfig}
                            sectionTypeEditable={false}
                            sectionEditable={false}
        />
    </div>

</div>
<div class="card mb-3">
    <div class="card-body">
        <h2>SORT Survey Questions</h2>
        <p>SORT questions are automatically added to your survey.</p>
    </div>
</div>
<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your demographic page</h2>
        <p>
            The demographic page of your survey can be configured below. We've provided some example demographic
            questions which can be freely customised.
        </p>
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
    <button type="submit" name="submit" value="Submit" class="btn btn-primary"><i class="bx bx-save"></i> Save</button>
</form>


<style>
</style>
