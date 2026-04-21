<script lang="ts" module>
  import DOMPurify from "dompurify";
  import {type SectionConfig, getDefaultSectionConfig} from "../../interfaces.ts";
  import type {MoveRequestHandler} from "./InputComponent.svelte";

  export type {MoveRequestHandler};

    </script>
<script lang="ts">
    import * as _ from "lodash-es"
    import {getDefaultFieldConfig, SectionTypes} from "../../interfaces.ts";
    import InputComponent from "./InputComponent.svelte";
    import EditableText from "./EditableText.svelte";
    import EditableTextArea from "./EditableTextArea.svelte";
    import type {SurveyResponse} from "../../interfaces.ts";




    interface Props {
        config: SectionConfig;
        value?: SurveyResponse[];
        editable?: boolean;
        viewerMode?: boolean;
        sectionTypeEditable?: boolean;
        sectionEditable?: boolean;
        displaySectionType?: boolean;
        sectionIndex?: number;
        onMoveRequest?: MoveRequestHandler | null;
        onDeleteSectionRequest?: () => void;
    }


    let {
        config = $bindable(),
        value = $bindable(),
        editable = false,
        viewerMode = false,
        sectionTypeEditable = true,
        sectionEditable = true,
        displaySectionType = true,
        sectionIndex = -1,
        onMoveRequest = null,
        onDeleteSectionRequest = () => {
        },
    }: Props = $props();

    //Insert missing keys
    config = {
        ...getDefaultSectionConfig(),
        ...config
    };

    // Keeps track of all field components
    let _fieldComponents: InputComponent[] = $state([])
    let fieldComponents: InputComponent[] = $derived(_fieldComponents.filter(Boolean));


    let fieldValues = $state(value !== null && value !== undefined ? value : []);
    $effect(() => {
        value = _.cloneDeep(fieldValues);
    });

    let textVal = $state();


    export function validate() {
        console.log("Validating section");
        let sectionValid = true;
        for (let i = 0; i < fieldComponents.length; i++) {
            if (!fieldComponents[i].validate()) {
                sectionValid = false;
            }
        }

        return sectionValid;
    }

    function addField() {
        config.fields.push(getDefaultFieldConfig())
    }

    function duplicateField(index: number) {
        // Defensive checks
        if (index < 0 || index >= config.fields.length) {
            throw new Error("Index out of bounds");
        }
        // Build a new array using the existing fields
        let updatedFields = [...config.fields];
        // Copy the field
        let _field = _.cloneDeep(updatedFields[index]);
        // User-created fields may be modified
        _field.readOnly = false;
        // Insert the new field at the end to avoid weird index issues
        updatedFields.push(_field)
        config.fields = updatedFields;
    }

    function deleteField(index: number) {
        config.fields.splice(index, 1);
    }


    function handleMoveRequest(srcSectionIndex: number,
                               srcFieldIndex: number,
                               destSectionIndex: number,
                               destFieldIndex: number) {
        if (onMoveRequest) {
            onMoveRequest(srcSectionIndex, srcFieldIndex, destSectionIndex, destFieldIndex);
        }
    }

    // Only allow fields to be deactivated in the demography section
    let canDisableFields = config.type == "demographic";

</script>

<div role="group" class="card mb-3"
     ondragover={(e) => {
       e.preventDefault();
       if(e?.dataTransfer)
        e.dataTransfer.dropEffect = "move";
     }}
     ondrop={(e) =>{
       e.preventDefault();
       e.stopPropagation();
       if(e?.dataTransfer) {
         const moveSource = JSON.parse(e.dataTransfer.getData("application/json"));
         onMoveRequest?.(moveSource.section, moveSource.field, sectionIndex, -1);
       }
     }}
>
    <div class="card-body">
        <div style="display: flex; justify-content: space-between; gap: 1em">
            <div style="flex: 1">
                <h2>
                    {#if editable}
                        <EditableText bind:value={config.title}/>
                    {:else}
                        {config.title}
                    {/if}
                </h2>
            </div>
            <div class="text-end">
                {#if displaySectionType}
                    {#if editable && sectionTypeEditable}
                        <select class="form-select" bind:value={config.type}>
                            {#each SectionTypes as sectionType (sectionType.value)}
                                <option value={sectionType.value}>{sectionType.label}</option>
                            {/each}
                        </select>
                    {:else}
                        <span class="badge text-bg-primary">Section type: {config.type}</span>
                    {/if}
                {/if}
            </div>
        </div>


        <div class="row">
            <div class="col-12">
                <p style="width: 100%">
                    {#if editable }
                        <EditableTextArea bind:value={config.description}/>
                    {:else}
                        {@html DOMPurify.sanitize(config.description)}
                    {/if}
                </p>
            </div>


        </div>


        {#each config.fields as field, index (index)}
            <div class="mb-3">
                <InputComponent
                        bind:config={config.fields[index]}
                        editable={editable}
                        viewerMode={viewerMode}
                        onDuplicateRequest={()=>{duplicateField(index)}}
                        onDeleteRequest={()=>{deleteField(index)}}
                        bind:value={fieldValues[index]}
                        bind:this={_fieldComponents[index]}
                        sectionIndex={sectionIndex}
                        fieldIndex={index}
                        onMoveRequest={handleMoveRequest}
                        canDisableFields={canDisableFields}
                />
            </div>
        {/each}

        {#if editable}
            <div class="d-flex justify-content-between">
                <button class="btn btn-primary" onclick={addField}><i class="bx bx-plus"></i> Add field</button>
                <div></div>
                {#if sectionEditable}
                    <button class="btn btn-danger" onclick={() => {onDeleteSectionRequest()}}><i
                            class="bx bxs-trash"></i> Delete section
                    </button>
                {/if}
            </div>
        {/if}
    </div>
</div>


