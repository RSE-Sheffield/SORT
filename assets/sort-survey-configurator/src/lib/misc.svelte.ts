import * as _ from 'lodash';

export function getDataInElem(elementId: string, defaultData: any){
    let elem = document.getElementById(elementId);
    let outputData = null;
    if(elem && elem.textContent != null && JSON.parse(elem.textContent)){
        outputData = JSON.parse(elem.textContent);
    }
    else{
        outputData = defaultData;
    }

    return _.cloneDeep(outputData);
}
