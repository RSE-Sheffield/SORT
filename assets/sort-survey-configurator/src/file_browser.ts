import { mount } from 'svelte'
import {getDataInElem} from "./lib/misc.svelte.js";
import {type FileDescriptionType} from "./lib/interfaces.ts"
import FileBrowserApp from "./lib/components/FileBrowser.svelte";

const csrf: string = getDataInElem("csrf", []);
const filesList: FileDescriptionType[] = getDataInElem("filesListData", []);

const matchingElements = document.querySelectorAll('.sort-file-browser')
for(let i = 0; i < matchingElements.length; i++){
    const elem = matchingElements[i];
    const app = mount(FileBrowserApp, {
        target: elem,
        props: { filesList: filesList, csrf: csrf}
    });

}
