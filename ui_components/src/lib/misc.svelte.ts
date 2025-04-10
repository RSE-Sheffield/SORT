import * as _ from "lodash-es";
import {
    type FieldConfig,
    type FieldStats,
    type SectionConfig,
    type SurveyConfig,
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

export function generateStatsFromSurveyResponses(config: SurveyConfig, responses: []) {
    if (config === null ||
        responses === null ||
        responses === undefined ||
        responses.length < 1)
        return null;

    const stats: SurveyStats = {sections: []};
    for (let si = 0; si < config.sections.length; si++) {
        // Stats for each section
        const sectionConfig: SectionConfig = config.sections[si];
        const fieldStats: FieldStats[] = [];
        for (let fi = 0; fi < sectionConfig.fields.length; fi++) {
            // Stats for each field
            const fieldConfig = sectionConfig.fields[fi];
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
            }
        }
        stats.sections.push({
            fields: fieldStats
        })
    }
    return stats;
}

function fieldStatsForText(fieldConfig: FieldConfig, si: number, fi: number, responses: []): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        values.push(responses[ri][si][fi])
    }
    return {values: values}
}

function fieldStatsForSingleOption(fieldConfig: FieldConfig, si: number, fi: number, responses: []): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        values.push(responses[ri][si][fi])
    }
    const fieldStats: FieldStats = {
        histogram: histogramFromConfigAndValues(fieldConfig, values)
    }

    genNumericFieldStats(fieldConfig, values, fieldStats);

    return fieldStats;
}

function fieldStatsForMultiOption(fieldConfig: FieldConfig, si: number, fi: number, responses: []): FieldStats {
    const values: string[] = [];
    for (let ri = 0; ri < responses.length; ri++) {
        for (let oi = 0; oi < responses[ri][si][fi].length; oi++) {
            values.push(responses[ri][si][fi][oi])
        }
    }
    const fieldStats: FieldStats = {
        histogram: histogramFromConfigAndValues(fieldConfig, values)
    }

    genNumericFieldStats(fieldConfig, values, fieldStats);

    return fieldStats;
}

function fieldStatForLikert(fieldConfig: FieldConfig, si: number, fi: number, responses: []): FieldStats {

    // Build histogram for the likert table
    let allValues: string[] = [];
    const histograms: ValueCount[][] = [];
    for (let subi = 0; subi < fieldConfig.sublabels.length; subi++) {
        const values: string[] = [];
        for (let ri = 0; ri < responses.length; ri++) {
            values.push(responses[ri][si][fi][subi])
        }
        allValues = allValues.concat(values);
        histograms.push(histogramFromConfigAndValues(fieldConfig, values));
    }

    const fieldStats: FieldStats = {
        histograms: histograms
    }

    genNumericFieldStats(fieldConfig, allValues, fieldStats);

    return fieldStats;
}

function histogramFromConfigAndValues(fieldConfig: FieldConfig, values: string[]) {
    const valuesCountMap = new Map<string, number>();
    fieldConfig.options.map((value: string) => {
        valuesCountMap.set(value, 0);
    });
    for (let i = 0; i < values.length; i++) {
        valuesCountMap.set(values[i], (valuesCountMap.get(values[i]) ?? 0) + 1);
    }
    const valuesHistogram: ValueCount[] = [];
    fieldConfig.options.map((value) => {
        valuesHistogram.push({option: value, count: (valuesCountMap.get(value) ?? 0)})
    })
    return valuesHistogram
}

function genNumericFieldStats(fieldConfig: FieldConfig, values: string[], fieldStats: FieldStats) {
    if (fieldOptionsAreNumeric(fieldConfig)) {
        const valuesNum = values.map(Number);
        fieldStats.areValuesNumeric = true;
        fieldStats.mean = _.mean(valuesNum);
        fieldStats.max = _.max(valuesNum);
        fieldStats.min = _.min(valuesNum);
    }
}


function fieldOptionsAreNumeric(fieldConfig: FieldConfig) {
    return fieldConfig.options.every((value) => {
        return !isNaN(Number(value)) && !isNaN(parseFloat(value));
    });
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

export function formatNumber(num: number) {
    return numFormat.format(num)
}

type ColourRange = {
    colour: string;
    textColour: string;
    min: number;
    max: number;
}

const colourRange: ColourRange[] = [
    {
        colour: "#d7191c",
        textColour: "#FFF",
        min: 0,
        max: 1.5,
    },
    {
        colour: "#fdae61",
        textColour: "#000",
        min: 1.5,
        max: 2.5,
    },
    {
        colour: "#abd9e9",
        textColour: "#000",
        min: 2.5,
        max: 3.5,
    },
    {
        colour: "#74add1",
        textColour: "#000",
        min: 3.5,
        max: 4.5,
    },
    {
        colour: "#2c7bb6",
        textColour: "#FFF",
        min: 4.5,
        max: 5.5,
    },
]

export function getColourForMeanValue(mean: number): string {
    for (let i = 0; i < colourRange.length; i++) {
        if (mean >= colourRange[i].min && mean <= colourRange[i].max)
            return colourRange[i].colour;
    }
    return colourRange[0].colour;
}

export function getTextColourForMeanValue(mean: number): string {
    for (let i = 0; i < colourRange.length; i++) {
        if (mean >= colourRange[i].min && mean <= colourRange[i].max)
            return colourRange[i].textColour;
    }
    return colourRange[0].textColour;
}
