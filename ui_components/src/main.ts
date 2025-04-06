import { mount } from 'svelte'
import {type FileDescriptionType} from "./lib/interfaces.ts"
import {getDataInElem} from "./lib/misc.svelte.js";
import SmartTable from "./lib/components/SmartTable.svelte";
import SurveyConfigConsentDemographyApp from "./SurveyConfigConsentDemographyApp.svelte";
import SurveyResponseApp from "./SurveyResponseApp.svelte";
import FileBrowser from "./lib/components/FileBrowser.svelte";
import QuillEditor from "./lib/components/QuillEditor.svelte";

const csrf: string = getDataInElem("csrf", []);

function mapMatchedElement(selector: string, handler: (elem: HTMLElement)=> void){
    const matchingElements = document.querySelectorAll(selector);
    for(let i = 0; i < matchingElements.length; i++) {
        const elem = matchingElements[i] as HTMLElement;
        handler(elem);
    }
}


mapMatchedElement(".sort-consent-demography-config", (elem) =>{
    const consentConfigId = elem.dataset.jsonConsentConfigId;
    const demographyConfigId = elem.dataset.jsonDemographyConfigId;
    const consentConfig = getDataInElem(consentConfigId, {})
    const demographyConfig = getDataInElem(demographyConfigId, {})
    mount(SurveyConfigConsentDemographyApp, {
        target: elem,
        props: {
            csrf: csrf,
            initConsentConfig: consentConfig,
            initDemographyConfig: demographyConfig
        }
    });
});

mapMatchedElement(".sort-survey-response", (elem) => {
    const configId = elem.dataset.jsonConfigId;
    const config = getDataInElem(configId, {});
    const responseId = elem.dataset.jsonResponseId;
    const response = getDataInElem(responseId, []);
    mount(SurveyResponseApp, {
        target: elem,
        props: {
            csrf: csrf,
            initConfig: config,
            initResponse: response
        }
    });
});


mapMatchedElement(".sort-file-browser", (elem) => {
    const fileListDataId =elem.dataset.jsonId;
    const filesList: FileDescriptionType[] = getDataInElem(fileListDataId, []);
    mount(FileBrowser, {
        target: elem,
        props: { filesList: filesList, csrf: csrf}
    });
});

mapMatchedElement(".sort-smart-table", (elem) => {
    const updateUrl = elem.dataset.updateUrl;
    const plan = elem.dataset.plan;
    mount(SmartTable, {
        target: elem,
        props: {data: plan, updateUrl: updateUrl, csrf: csrf}
    });
});

mapMatchedElement(".sort-quill-editor", (elem) => {
    const updateUrl = elem.dataset.updateUrl;
    const initContents = elem.dataset.initContents;
    const viewOnly = !!elem.dataset.viewOnly
    mount(QuillEditor, {
        target: elem,
        props: {
            csrf: csrf,
            updateUrl: updateUrl,
            initContents: initContents,
            viewOnly: viewOnly
        }
    });
});
