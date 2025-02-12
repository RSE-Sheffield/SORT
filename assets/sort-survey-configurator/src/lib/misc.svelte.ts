import * as _ from 'lodash';

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

/**
 * Get data from a script tag with the id elementId, this is created by django's filter json_cript
 * @param elementId ID of the script tag
 * @param defaultData Default data to use if the element or data does not exist
 */
export function getDataInElem(elementId: string, defaultData: any) {
    let elem = document.getElementById(elementId);
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
export function download(fileName:string, text:string) {
    var element = document.createElement('a');
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
let uniqueIdSet = new Set<string>();
let uniqueNameSet = new Set<string>();


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
        let randomText = prefix + generateString(numChars)
        if (!checkSet.has(randomText)) {
            return randomText;
        }
    }
}

export function getUniqueID(): string {
    return generateUniqueAndCheck(idPrefix, generateLength, uniqueIdSet);

}

export function getUniqueIDArray(length: number) {
    let outputIds = [];
    for (let i = 0; i < length; i++) {
        outputIds.push(generateUniqueAndCheck(idPrefix, generateLength, uniqueIdSet))
    }
    return outputIds
}

export function getUniqueName(): string {
    return generateUniqueAndCheck(namePrefix, generateLength, uniqueNameSet);
}
