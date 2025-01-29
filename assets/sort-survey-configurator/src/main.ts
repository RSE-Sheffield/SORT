import { mount } from 'svelte'
import App from './App.svelte'
import SurveyConfigConsentDemographyApp from "./SurveyConfigConsentDemographyApp.svelte";
import SurveyResponseApp from "./SurveyResponseApp.svelte";

const app = mount(SurveyResponseApp, {
        target: document.getElementById('app')!,
    });

export default app;
