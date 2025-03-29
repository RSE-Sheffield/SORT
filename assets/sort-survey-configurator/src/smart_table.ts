import { mount } from 'svelte'
import {getDataInElem} from "./lib/misc.svelte.js";
import SmartTable from "./lib/components/SmartTable.svelte";

const csrf: string = getDataInElem("csrf", []);


const matchingElements = document.querySelectorAll('.sort-smart-table')
for(let i = 0; i < matchingElements.length; i++){
    const elem = matchingElements[i];
    const updateUrl = elem.dataset.updateUrl;
    const plan = elem.dataset.plan;
    console.log(updateUrl);
    const app = mount(SmartTable, {
        target: elem,
        props: {data: plan, updateUrl: updateUrl, csrf: csrf}
    });

}
