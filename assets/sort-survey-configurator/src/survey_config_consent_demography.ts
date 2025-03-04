import { mount } from 'svelte'
import SurveyConfigConsentDemographyApp from "./SurveyConfigConsentDemographyApp.svelte";

const app = mount(SurveyConfigConsentDemographyApp, {
        target: document.getElementById('app')!,
    });

export default app;
