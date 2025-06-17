<script lang="ts">
    import SurveyConfigurator from "./lib/components/SurveyConfigurator.svelte";

    //Import data from other script blocks on page (for django)
    //otherwise use the default config
    let {csrf, initConsentConfig, initDemographyConfig, initSurveyBodyPath} = $props();

    let consentConfig = $state(initConsentConfig);
    let demographyConfig = $state(initDemographyConfig);
    let surveyBodyPath = $state(initSurveyBodyPath);

    let consentConfigStr = $derived(JSON.stringify(consentConfig));
    let demographyConfigStr = $derived(JSON.stringify(demographyConfig));
</script>



<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your welcome and consent page</h2>

        <p>
            The introduction page of your survey page can be configured below. We've provided a default consent page
            which
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
        <label class="form-label">Select who this survey will target:
        <select class="form-select" bind:value={surveyBodyPath}>
            <option value="Nurses">Nurses</option>
            <option value="Midwives">Midwives</option>
            <option value="NMAHPs">NMAHPs</option>
        </select>
        </label>

    </div>
</div>
<div class="card mb-3">
    <div class="card-body">
        <h2>Configure your demographic page</h2>
        <p>
            The demographic page of your survey can be configured below. We've provided some example demographic
            questions which can be freely customised.
        </p>
        <p>
            The in-built demographics fields may not be modified and are labelled "Read only".
        </p>
        <div class="alert alert-warning" role="alert">
            <i class='bx bxs-error' ></i> Please avoid collecting personally identifiable information. If needed, instead of
            collecting names, emails or addresses, it is recommended to collect IDs that can be used to identify
            participants from within the your organisation instead.
        </div>
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
    <input type="hidden" name="survey_body_path" value="{surveyBodyPath}"/>
    <button type="submit" name="submit" value="Submit" class="btn btn-primary"><i class="bx bx-save"></i> Save</button>
</form>


<style>
</style>
