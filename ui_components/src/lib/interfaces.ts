/**
 * The type of data an input text field is to represent,
 * used in presentation and validation.
 */
export enum TextType {
    plain = "PLAIN_TEXT",
    email = "EMAIL_TEXT",
    integer = "INTEGER_TEXT",
    decimals = "DECIMALS_TEXT"
}


export interface FileDescription {
    name: string,
    deleteUrl: string,
    fileUrl: string,
}

export type {FileDescription as FileDescriptionType}

export type FieldType = "text" | "textarea" | "checkbox" | "radio" | "select" | "likert";

export type FieldConfig = {
    type: FieldType;
    label: string;
    description: string;
    required: boolean;
    sublabels: string[];
    options: string[];
    // Text and Textarea options
    enforceValueConstraints?: boolean;
    maxNumChar?: number;
    minNumValue?: number;
    maxNumValue?: number;
    textType?: TextType;
    readOnly?: boolean;
    disabled?: boolean;
    hasOtherOption?: boolean; // Freetext option only for Radio components
}

export function getDefaultFieldConfig(): FieldConfig {
    return {
        type: "text",
        label: "New Question",
        description: "",
        required: true,
        sublabels: [], // Subquestions for likert
        options: [], // Options for Checkbox, Radio, Select and Likert
        // Text and Textarea options
        enforceValueConstraints: false,
        maxNumChar: 500,
        minNumValue: 0,
        maxNumValue: 100,
        textType: TextType.plain,
        readOnly: false,
        disabled: false,
        hasOtherOption: false,
    };
}

export type SectionConfig = {
    title: string;
    type: "sort" | "demographic" | "consent";
    description: string;
    fields: FieldConfig[];
}

export const SectionTypes = [
    {label: "Consent", value: "consent"},
    {label: "SORT", value: "sort"},
    {label: "Demographic", value: "demographic"}
];

export function getDefaultSectionConfig() {
    return {
        title: "New section",
        description: "Section description",
        type: "consent",
        fields: []
    } as SectionConfig;
}

export type SurveyConfig = {
    sections: SectionConfig[];
}

export function getDefaultSurveyConfig(){
    return {
        sections: [],
    } as SurveyConfig;

}


/**
 * Represents the output of each input component in the survey
 * they either return a single string value (text, textarea, radio, select) or an array of values (checkbox, likert)
 */
export type SurveyResponse = string | string[];
/**
 * Represent a batch of survey responses with indices [batch/response Index][sectionIndex][fieldIndex]
 */
export type SurveyResponseBatch = SurveyResponse[][][];

export type ValueCount = {
    option: string;
    count: number
}

export type FieldStats = {
    values?: string[];
    areValuesNumeric?: boolean;
    histogram?: ValueCount[];
    histograms?: ValueCount[][];
    mean?: number;
    min?: number;
    max?: number;
    mode?: number;
}

export type SectionStats = {
    fields: FieldStats[];
}

export type SurveyStats = {
    sections: SectionStats[];
}





