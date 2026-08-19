import * as _ from "lodash-es";
import {
    type FieldConfig,
    type FieldStats,
    type SectionConfig,
    type SurveyConfig, type SurveyResponse, type SurveyResponseBatch,
    type SurveyStats,
    type ValueCount
} from "./interfaces.ts";


/**
 * Get data from a script tag with the id elementId, this is created by django's filter json_cript
 * @param elementId ID of the script tag
 * @param defaultData Default data to use if the element or data does not exist
 */
export function getDataInElem(elementId: string | null | undefined, defaultData: unknown) {
    if (elementId === null || elementId === undefined)
        return defaultData;

    const elem = document.getElementById(elementId);
    let outputData = null;
    if (elem && elem.textContent != null && JSON.parse(elem.textContent)) {
        outputData = JSON.parse(elem.textContent);
    } else {
        outputData = defaultData;
    }

    return _.cloneDeep(outputData);
}

/**
 * Triggers a browser file download where the content is the provided text. fileName as default file name
 * for saving.
 * @param fileName
 * @param text
 */
export function download(fileName: string, text: string) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', fileName);

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}


/**
 * Generation of unique names or ids for labels and input fields
 */

const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const idPrefix = "sort_ui_auto_id_";
const namePrefix = "sort_ui_auto_name_";
const generateLength = 16;
const uniqueIdSet = new Set<string>();
const uniqueNameSet = new Set<string>();


function generateString(length: number) {
    let result = '';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }

    return result;
}

function generateUniqueAndCheck(prefix: string, numChars: number, checkSet: Set<string>) {
    while (true) {
        const randomText = prefix + generateString(numChars)
        if (!checkSet.has(randomText)) {
            return randomText;
        }
    }
}

export function getUniqueID(): string {
    return generateUniqueAndCheck(idPrefix, generateLength, uniqueIdSet);

}

export function getUniqueIDArray(length: number) {
    const outputIds = [];
    for (let i = 0; i < length; i++) {
        outputIds.push(generateUniqueAndCheck(idPrefix, generateLength, uniqueIdSet))
    }
    return outputIds
}

export function getUniqueName(): string {
    return generateUniqueAndCheck(namePrefix, generateLength, uniqueNameSet);
}


/**
 * Action callback for when the user click outside of the specified element
 * @param node
 * @param handler
 */
export function clickOutside(node: HTMLElement, handler: () => void) {
    const handleClick = (event: MouseEvent) => {
        if (event.target && !node.contains(event.target as Element)) {
            handler();
        }
    };

    document.addEventListener('click', handleClick, true);

    return {
        destroy() {
            document.removeEventListener('click', handleClick, true);
        }
    };
}

/**
 * Read a single answer from a batch of responses.
 *
 * Stored responses do not always match the survey configuration: responses submitted
 * before `Survey.response_schema` validation was introduced, or a survey whose
 * configuration was regenerated from the template files, can hold fewer sections or
 * fields than the configuration describes. Return `undefined` for those so the caller
 * can skip the answer instead of throwing.
 */
function getAnswer(responses: SurveyResponseBatch, ri: number, si: number, fi: number) {
    return responses[ri]?.[si]?.[fi];
}

/**
 * True when an answer is present, i.e. the response actually holds a value here.
 */
function hasAnswer(answer: SurveyResponse | undefined): answer is SurveyResponse {
    return answer !== undefined && answer !== null;
}

/**
 * Coerce an answer to the list of selected options.
 *
 * Multi-option fields (checkbox, likert) store a list, but a malformed response may
 * hold a bare string. Wrap it rather than iterating over its characters.
 */
function answerAsList(answer: SurveyResponse | undefined): string[] {
    if (!hasAnswer(answer)) return [];
    return Array.isArray(answer) ? answer : [answer];
}

export function generateStatsFromSurveyResponses(config: SurveyConfig, responses: SurveyResponseBatch) {
    if (config === null ||
        config === undefined ||
        responses === null ||
        responses === undefined ||
        responses.length < 1)
        return null;

    const stats: SurveyStats = {sections: []};
    const sections = config.sections ?? [];
    for (let si = 0; si < sections.length; si++) {
        // Stats for each section
        const sectionConfig: SectionConfig = sections[si];
        const fieldStats: FieldStats[] = [];
        const fields = sectionConfig.fields ?? [];
        for (let fi = 0; fi < fields.length; fi++) {
            // Stats for each field
            const fieldConfig = fields[fi];
            switch (fieldConfig.type) {
                case "likert":
                    fieldStats.push(fieldStatForLikert(fieldConfig, si, fi, responses));
                    break;
                case "select":
                case "radio":
                    fieldStats.push(fieldStatsForSingleOption(fieldConfig, si, fi, responses));
                    break;
                case "checkbox":
                    fieldStats.push(fieldStatsForMultiOption(fieldConfig, si, fi, responses));
                    break;
                case "text":
                case "textarea":
                    fieldStats.push(fieldStatsForText(fieldConfig, si, fi, responses));
                    break;
                default:
                    // Keep one entry per configured field: consumers index these stats by
                    // the *configuration* field index, so skipping an unrecognised field
                    // type would silently shift every later field in this section.
                    fieldStats.push({});
                    break;
            }
        }
        stats.sections.push({
            fields: fieldStats
        })
    }
    return stats;
}

function fieldStatsForText(fieldConfig: FieldConfig, si: number, fi: number, responses: SurveyResponseBatch): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        const answer = getAnswer(responses, ri, si, fi);
        if (!hasAnswer(answer)) continue;
        values.push(answer as string)
    }
    return {values: values}
}

function fieldStatsForSingleOption(fieldConfig: FieldConfig, si: number, fi: number, responses: SurveyResponseBatch): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        const answer = getAnswer(responses, ri, si, fi);
        if (!hasAnswer(answer)) continue;
        values.push(answer as string)
    }
    const fieldStats: FieldStats = {
        histogram: histogramFromConfigAndValues(fieldConfig, values)
    }

    genNumericFieldStats(values, fieldStats);

    return fieldStats;
}

function fieldStatsForMultiOption(fieldConfig: FieldConfig, si: number, fi: number, responses: SurveyResponseBatch): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        values.push(...answerAsList(getAnswer(responses, ri, si, fi)));
    }
    const fieldStats: FieldStats = {
        histogram: histogramFromConfigAndValues(fieldConfig, values)
    }

    genNumericFieldStats(values, fieldStats);

    return fieldStats;
}

function fieldStatForLikert(fieldConfig: FieldConfig, si: number, fi: number, responses: SurveyResponseBatch): FieldStats {

    // Build histogram for the likert table
    let allValues: string[] = [];
    const histograms: ValueCount[][] = [];
    const sublabels = fieldConfig.sublabels ?? [];
    for (let subi = 0; subi < sublabels.length; subi++) {
        const values: string[] = [];
        for (let ri = 0; ri < responses.length; ri++) {
            const value = answerAsList(getAnswer(responses, ri, si, fi))[subi];
            if (value === undefined || value === null) continue;
            values.push(value)
        }
        allValues = allValues.concat(values);
        histograms.push(histogramFromConfigAndValues(fieldConfig, values));
    }

    const fieldStats: FieldStats = {
        histograms: histograms
    }

    genNumericFieldStats(allValues, fieldStats);

    return fieldStats;
}

function histogramFromConfigAndValues(fieldConfig: FieldConfig, values: string[]) {
    // eslint-disable-next-line svelte/prefer-svelte-reactivity -- local, non-reactive collection
    const valuesCountMap = new Map<string, number>();
    // Histogram from options in the configuration
    (fieldConfig.options ?? []).map((value: string) => {
        valuesCountMap.set(value, 0);
    });

    // Add histogram entry for custom "other" options
    if(fieldConfig.hasOtherOption){
        values.map(val => {
            if(!valuesCountMap.has(val)){
                valuesCountMap.set(val, 0);
            }
        });
    }

    // Increment histogram count by going through all the values
    for (let i = 0; i < values.length; i++) {
        valuesCountMap.set(values[i], (valuesCountMap.get(values[i]) ?? 0) + 1);
    }
    // Convert to correct structure
    const valuesHistogram: ValueCount[] = [];
    for(const [option, count] of valuesCountMap){
        valuesHistogram.push({option: option, count: count});
    }
    return valuesHistogram
}

function genNumericFieldStats(values: string[], fieldStats: FieldStats) {
    // An empty set of values tells us nothing, so do not report a mean of NaN for it.
    const fieldIsNumeric = values.length > 0 && values.every(val => isOptionNumeric(val));
    if (fieldIsNumeric) {
        const valuesNum = values.map(Number);
        fieldStats.areValuesNumeric = true;
        fieldStats.mean = _.mean(valuesNum);
        fieldStats.max = _.max(valuesNum);
        fieldStats.min = _.min(valuesNum);
    }
}

function isOptionNumeric(option: string){
    return !isNaN(Number(option)) && !isNaN(parseFloat(option));
}

export function getHighestHistogramValue(histogram: ValueCount[]) {
    let highestVal = 0;
    for (let i = 0; i < histogram.length; i++) {
        const val = Number(histogram[i].option);
        if (val > highestVal)
            highestVal = val;
    }
    return highestVal;
}

export function getHistogramMean(histogram: ValueCount[]) {
    let totalCount = 0;
    let valueSum = 0;
    histogram.map(value => {
        totalCount += value.count;
        valueSum += Number(value.option) * value.count;
    })
    return valueSum / totalCount;
}

const numFormat = Intl.NumberFormat("en-GB", {maximumFractionDigits: 3})

export function formatNumber(num: number | undefined | null) {
    if (num === undefined || num === null || Number.isNaN(num)) return "";
    return numFormat.format(num)
}

/**
 * Readiness level boundaries
 *
 * Scores are mapped to labels using midpoint boundaries:
 * - [0.0, 0.5): "Not yet planned"
 * - [0.5, 1.5): "Planned"
 * - [1.5, 2.5): "Early progress"
 * - [2.5, 3.5): "Substantial progress"
 * - [3.5, 4.0]: "Established"
 */
const MATURITY_BOUNDARIES = {
    PLANNED: 0.5,
    EARLY_PROGRESS: 1.5,
    SUBSTANTIAL_PROGRESS: 2.5,
    ESTABLISHED: 3.5
} as const;

/**
 * Readiness level labels
 */
export const MATURITY_LABELS = {
    NOT_YET_PLANNED: "Not yet planned",
    PLANNED: "Planned",
    EARLY_PROGRESS: "Early progress",
    SUBSTANTIAL_PROGRESS: "Substantial progress",
    ESTABLISHED: "Established"
} as const;

/**
 * Shown in place of a maturity label when there is no score to describe, e.g. a section
 * whose responses hold no numeric answers.
 */
export const MATURITY_LABEL_UNKNOWN = "Not available";

/**
 * Maturity label type - union of all possible maturity level labels
 */
export type MaturityLabel = typeof MATURITY_LABELS[keyof typeof MATURITY_LABELS];

type ColourRange = {
    colour: string;
    textColour: string;
    min: number;
    max: number;
}

const colourRange: ColourRange[] = [
    {
        colour: "#ccccdd",
        textColour: "#000",
        min: 0,
        max: MATURITY_BOUNDARIES.PLANNED,
    },
    {
        colour: "#aa99cc",
        textColour: "#000",
        min: MATURITY_BOUNDARIES.PLANNED,
        max: MATURITY_BOUNDARIES.EARLY_PROGRESS,
    },
    {
        colour: "#abd9e9",
        textColour: "#000",
        min: MATURITY_BOUNDARIES.EARLY_PROGRESS,
        max: MATURITY_BOUNDARIES.SUBSTANTIAL_PROGRESS,
    },
    {
        colour: "#74add1",
        textColour: "#000",
        min: MATURITY_BOUNDARIES.SUBSTANTIAL_PROGRESS,
        max: MATURITY_BOUNDARIES.ESTABLISHED,
    },
    {
        colour: "#440099",
        textColour: "#FFF",
        min: MATURITY_BOUNDARIES.ESTABLISHED,
        max: 4.5,
    },
]

/** Cell background used when there is no mean score to colour by */
const UNKNOWN_MEAN_COLOUR = "transparent";
/** Text colour used alongside UNKNOWN_MEAN_COLOUR */
const UNKNOWN_MEAN_TEXT_COLOUR = "inherit";

export function getColourForMeanValue(mean: number | undefined | null): string {
    // No score: leave the cell unshaded rather than implying the lowest maturity level
    if (mean === undefined || mean === null || Number.isNaN(mean)) return UNKNOWN_MEAN_COLOUR;
    for (let i = 0; i < colourRange.length; i++) {
        // Use exclusive upper bound for all ranges except the last one
        const matchesRange = i === colourRange.length - 1
            ? mean >= colourRange[i].min && mean <= colourRange[i].max
            : mean >= colourRange[i].min && mean < colourRange[i].max;

        if (matchesRange) {
            return colourRange[i].colour;
        }
    }
    return colourRange[0].colour;
}

export function getTextColourForMeanValue(mean: number | undefined | null): string {
    if (mean === undefined || mean === null || Number.isNaN(mean)) return UNKNOWN_MEAN_TEXT_COLOUR;
    for (let i = 0; i < colourRange.length; i++) {
        // Use exclusive upper bound for all ranges except the last one
        const matchesRange = i === colourRange.length - 1
            ? mean >= colourRange[i].min && mean <= colourRange[i].max
            : mean >= colourRange[i].min && mean < colourRange[i].max;

        if (matchesRange) {
            return colourRange[i].textColour;
        }
    }
    return colourRange[0].textColour;
}

/**
 * Get the readiness level label for a given mean score.
 *
 * A missing score (undefined, null or NaN) yields MATURITY_LABEL_UNKNOWN rather than an
 * error: a field whose answers are absent or non-numeric has no mean, and that must not
 * take down the whole report.
 *
 * @param score The maturity score (0.0 to 4.0 inclusive), or undefined when unknown
 * @returns The human-readable maturity level label
 * @throws {TypeError} If score is not a number
 * @throws {RangeError} If score is a number outside the valid range [0, 4]
 *
 * @example
 * getSortMaturityLabel(0.3);        // "Not yet planned"
 * getSortMaturityLabel(2.8);        // "Substantial progress"
 * getSortMaturityLabel(undefined);  // "Not available"
 */
export function getSortMaturityLabel(score: number | undefined | null): MaturityLabel | typeof MATURITY_LABEL_UNKNOWN {
    // Validate input
    // Reject string inputs
    if (typeof score === 'string') {
        throw new TypeError(`Score must be a number, not a string. Got: ${score}`);
    }
    // No score to describe
    if (score === undefined || score === null || Number.isNaN(score)) {
        return MATURITY_LABEL_UNKNOWN;
    }
    // Reject numbers out of range
    if (!Number.isFinite(score) || score < 0.0 || score > 4.0) {
        throw new RangeError(`Score must be between 0 and 4, got: ${score}`);
    }
    // Use midpoint boundaries between adjacent readiness levels
    if (score < MATURITY_BOUNDARIES.PLANNED) return MATURITY_LABELS.NOT_YET_PLANNED;
    if (score < MATURITY_BOUNDARIES.EARLY_PROGRESS) return MATURITY_LABELS.PLANNED;
    if (score < MATURITY_BOUNDARIES.SUBSTANTIAL_PROGRESS) return MATURITY_LABELS.EARLY_PROGRESS;
    if (score < MATURITY_BOUNDARIES.ESTABLISHED) return MATURITY_LABELS.SUBSTANTIAL_PROGRESS;
    return MATURITY_LABELS.ESTABLISHED;
}
