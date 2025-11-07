<script lang="ts" module>
    import type {SurveyConfig} from "../interfaces.ts";

    export function getDefaultSurveyConfig(){
        return {
            sections: [],
        } as SurveyConfig;

    }
</script>
<script lang="ts">

    import * as _ from "lodash-es"
    import SectionComponent, {getDefaultSectionConfig} from "./input/SectionComponent.svelte";

    interface Props {
        config: SurveyConfig;
        editable?: boolean;
        sectionTypeEditable?: boolean;
        sectionEditable?: boolean;
    }

    let {
        config = $bindable(),
        editable = true,
        sectionTypeEditable = true,
        sectionEditable = true,
    }: Props = $props();

    if(config === null || config === undefined){
        config = getDefaultSurveyConfig();
    } else if(!("sections" in config)){
        config = {
            ...getDefaultSurveyConfig(),
            ...config
        };
    }

    // Keeps track of all section components
    // when components are deleted the derived property filters this out
    let _sectionComponents: SectionComponent[] = $state([]);
    let sectionComponents = $derived(_sectionComponents.filter(Boolean));

    function addSection() {
        config.sections.push(getDefaultSectionConfig());
    }

    function deleteSection(index: number){
        config.sections.splice(index, 1);
    }

    function handleMoveRequest(srcSectionIndex: number, srcFieldIndex: number, destSectionIndex: number, destFieldIndex: number){

        if(!editable || srcSectionIndex < 0 || destSectionIndex < 0 || srcFieldIndex < 0)
            return;

        if(srcSectionIndex === destSectionIndex && destFieldIndex < 0)
            return; // Don't move if dropped into the same section

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
                      sectionEditable={sectionEditable}
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


