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

export type FieldConfig = {
    type: "text" | "textarea" | "checkbox" | "radio" | "select" | "likert";
    label: string;
    description: string;
    required: boolean;
    sublabels: string[];
    options: string[];
    // Text and Textarea options
    enforceValueConstraints?: boolean,
    maxNumChar?: number,
    minNumValue?: number,
    maxNumValue?: number,
    textType?: TextType,
}

export type SectionConfig = {
    title: string;
    type: "sort" | "demographic" | "consent";
    description: string;
    fields: FieldConfig[];
}

export type SurveyConfig = {
    sections: SectionConfig[];
}

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
