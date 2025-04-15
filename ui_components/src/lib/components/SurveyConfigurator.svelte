<script lang="ts">

    import * as _ from "lodash-es"
    import SectionComponent, {getDefaultSectionConfig} from "./input/SectionComponent.svelte";

    let {
        config = $bindable(),
        editable = true,
        sectionTypeEditable = true,
        sectionEditable = true,
    } = $props();

    if(config == null || config === undefined){
        config = {}
    }

    if(!("sections" in config)){
        config.sections = [];
    }

    // Keeps track of all section components
    // when components are deleted the derived property filters this out
    let _sectionComponents = $state([]);
    let sectionComponents = $derived(_sectionComponents.filter(Boolean));

    function addSection() {
        config.sections.push(getDefaultSectionConfig());
    }

    function deleteSection(index){
        config.sections.splice(index, 1);
    }

    function handleMoveRequest(srcSectionIndex, srcFieldIndex, destSectionIndex, destFieldIndex){
        if(!editable || srcSectionIndex < 0 || destSectionIndex < 0 || srcFieldIndex < 0)
            return;

        if(destFieldIndex >= 0){
            // Move within or between sections with existing elements
            let fieldItem = _.cloneDeep(config.sections[srcSectionIndex].fields[srcFieldIndex]);
            config.sections[srcSectionIndex].fields.splice(srcFieldIndex, 1);
            config.sections[destSectionIndex].fields.splice(destFieldIndex, 0, fieldItem)

        }
        else {
            // Move to an empty section
            let fieldItem = _.cloneDeep(config.sections[srcSectionIndex].fields[srcFieldIndex]);
            config.sections[srcSectionIndex].fields.splice(srcFieldIndex, 1);
            config.sections[destSectionIndex].fields = [...config.sections[destSectionIndex].fields, fieldItem];
        }
    }


</script>



{#each config.sections as section, index (index)}
    <SectionComponent bind:config={config.sections[index]}
                      editable={editable}
                      sectionTypeEditable={sectionTypeEditable}
                      bind:this={_sectionComponents[index]}
                      sectionIndex={index}
                      onMoveRequest={handleMoveRequest}
                      onDeleteSectionRequest={()=>{deleteSection(index)}}
    />
{/each}

{#if sectionEditable}
<div class="mb-3">
    <button class="btn btn-primary" onclick={addSection}>Add section</button>
</div>
{/if}


