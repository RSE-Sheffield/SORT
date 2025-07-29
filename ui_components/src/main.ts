import { mount } from 'svelte'
import {type FileDescriptionType, type SurveyConfig, type SurveyResponseBatch} from "./lib/interfaces.ts"
import {generateStatsFromSurveyResponses, getDataInElem} from "./lib/misc.svelte.js";
import SmartTable from "./lib/components/SmartTable.svelte";
import SurveyConfigConsentDemographyApp from "./SurveyConfigConsentDemographyApp.svelte";
import SurveyResponseApp from "./SurveyResponseApp.svelte";
import FileBrowser from "./lib/components/FileBrowser.svelte";
import RichtextFormField from "./lib/components/RichtextFormField.svelte";
import SurveyResponseViewerApp from "./lib/components/SurveyResponseViewerApp.svelte";
import SurveySectionDataView from "./lib/components/SurveySectionDataView.svelte";
import SortSummaryMatrix from "./lib/components/SortSummaryMatrix.svelte";

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
    const surveyBodyPath = elem.dataset.surveyBodyPath;
    const consentConfig = getDataInElem(consentConfigId, {})
    const demographyConfig = getDataInElem(demographyConfigId, {})
    mount(SurveyConfigConsentDemographyApp, {
        target: elem,
        props: {
            csrf: csrf,
            initConsentConfig: consentConfig,
            initDemographyConfig: demographyConfig,
            initSurveyBodyPath: surveyBodyPath
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
            initResponse: response,
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
    const viewOnly = !!elem.dataset.viewOnly;
    mount(SmartTable, {
        target: elem,
        props: {data: plan, updateUrl: updateUrl, csrf: csrf, viewOnly: viewOnly}
    });
});

mapMatchedElement(".sort-richtext-field", (elem) => {
    const updateUrl = elem.dataset.updateUrl;
    const initContents = elem.dataset.initContents;
    const viewOnly = !!elem.dataset.viewOnly
    mount(RichtextFormField, {
        target: elem,
        props: {
            csrf: csrf,
            updateUrl: updateUrl,
            initContents: initContents,
            viewOnly: viewOnly
        }
    });
});



mapMatchedElement(".sort-response-viewer", (elem) => {
    const csvUrl = elem.dataset.csvUrl ?? "";
    const configId = elem.dataset.jsonConfigId;
    const responsesId = elem.dataset.jsonResponsesId;
    const config = getDataInElem(configId, {});
    const responses: SurveyResponseBatch = getDataInElem(responsesId, []);
    mount(SurveyResponseViewerApp, {
        target: elem,
        props: {
            config: config,
            responses: responses,
            csvDownloadUrl: csvUrl,
        }
    });
});

mapMatchedElement(".sort-response-section-viewer", (elem) => {
    const sectionIndex = Number(elem.dataset.sectionIndex);
    const configId = elem.dataset.jsonConfigId;
    const responsesId = elem.dataset.jsonResponsesId;
    // Get readiness-level descriptions for all sections
    const readinessDescriptionsId = elem.dataset.jsonReadinessDescriptionsId;
    const readinessDescriptionsAllSections = getDataInElem(readinessDescriptionsId, []);
    // Readiness descriptions for just this section (levels 0 to 4)
    const readinessDescriptions = readinessDescriptionsAllSections[sectionIndex-1];
    const config = getDataInElem(configId, {}) as SurveyConfig;
    const responses: SurveyResponseBatch = getDataInElem(responsesId, []) as [];
    const surveyStats = generateStatsFromSurveyResponses(config, responses);
    mount(SurveySectionDataView, {
        target: elem,
        props: {
            config: config,
            surveyStats: surveyStats,
            sectionIndex: sectionIndex,
            readinessDescriptions: readinessDescriptions,
        }
    });
});

mapMatchedElement(".sort-response-summary-matrix", (elem) => {
    const configId = elem.dataset.jsonConfigId;
    const responsesId = elem.dataset.jsonResponsesId;
    const config = getDataInElem(configId, {}) as SurveyConfig;
    const responses: SurveyResponseBatch = getDataInElem(responsesId, []) as [];
    const surveyStats = generateStatsFromSurveyResponses(config, responses)
    mount(SortSummaryMatrix, {
        target: elem,
        props: {
            config: config,
            surveyStats: surveyStats,
        }
    });
});
