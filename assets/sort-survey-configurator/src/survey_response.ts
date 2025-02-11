import { mount } from 'svelte'
import SurveyResponseApp from "./SurveyResponseApp.svelte";


const app = mount(SurveyResponseApp, {
        target: document.getElementById('app')!,
    });

export default app;
