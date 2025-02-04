<script lang="ts">

    import SectionComponent, {getDefaultSectionConfig} from "./input/SectionComponent.svelte";

    let {
        config = $bindable({sections: []}),
        editable = true,
        sectionTypeEditable = true,
        sectionEditable = true,

    } = $props();

    if(!("sections" in config)){
        config.sections = [];
    }

    // Keeps track of all section components
    // when components are deleted the derived property filters this out
    let _sectionComponents = $state([]);
    let sectionComponents = $derived(_sectionComponents.filter(Boolean));



    export function validate() {
        // for (let i in sectionComponents) {
        //     sectionComponents[i].validate();
        // }
    }

    export function getValue(){
        let sectionValues = [];
        for (let i = 0; i < sectionComponents.length; i++) {
            sectionValues.push(sectionComponents[i].getValue())
        }

        download("formValues.json", JSON.stringify(sectionValues, null, 2));

        return sectionValues;
    }

    export function getConfig() {
        download("config.json", JSON.stringify(config, null, 2));
    }

    function checkCurrentEditor(sectionIndex: number, fieldIndex: number, doEdit: boolean) {
        for (let i = 0; i < sectionComponents.length; i++) {
            if(doEdit){
                if(i == sectionIndex){
                sectionComponents[i].startEditAtIndex(fieldIndex);
                }else{
                    sectionComponents[i].stopEditingAll();
                }
            }
            else{
                sectionComponents[i].stopEditingAll();
            }


        }
    }

    function addSection() {
        config.sections.push(getDefaultSectionConfig());
    }

    function download(filename, text) {
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    }


</script>



{#each config.sections as section, index (index)}
    <SectionComponent bind:config={config.sections[index]}
                      editable={editable}
                      onEditRequest={(fieldIndex, doEdit)=>{checkCurrentEditor(index, fieldIndex, doEdit)}}
                      sectionTypeEditable={sectionTypeEditable}
                      bind:this={_sectionComponents[index]}
    />
{/each}

{#if sectionEditable}
<div class="mb-3">
    <button class="btn btn-primary" onclick={addSection}>Add section</button>
</div>
{/if}


