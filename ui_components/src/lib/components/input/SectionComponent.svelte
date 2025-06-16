<script lang="ts" module>
    import DOMPurify from "dompurify";
    import type {SectionConfig} from "../../interfaces.ts";

    export function getDefaultSectionConfig(): SectionConfig {
        return {
            title: "New section",
            description: "Section description",
            type: "consent",
            fields: []
        };
    }

    export const sectionTypes = [
        {label: "Consent", value: "consent"},
        {label: "SORT", value: "sort"},
        {label: "Demographic", value: "demographic"}
    ]
</script>
<script lang="ts">
    import * as _ from "lodash-es"
    import InputComponent, {getDefaultFieldConfig} from "./InputComponent.svelte";
    import EditableText from "./EditableText.svelte";
    import EditableTextArea from "./EditableTextArea.svelte";


    let {
        config = $bindable(),
        value = $bindable(),
        editable = false,
        viewerMode = false,
        sectionTypeEditable = true,
        displaySectionType = true,
        sectionIndex = -1,
        onMoveRequest = null,
        onDeleteSectionRequest = () => {
        },
    } = $props();

    //Insert missing keys
    let defultConfig = getDefaultSectionConfig()
    for (let key in defultConfig) {
        if (!(key in config)) {
            config[key] = defultConfig[key];
        }
    }

    // Keeps track of all field components
    let _fieldComponents = $state([])
    let fieldComponents = $derived(_fieldComponents.filter(Boolean));


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

    export function getValue() {
        let fieldValues = []
        for (let i = 0; i < fieldComponents.length; i++) {
            fieldValues.push(fieldComponents[i].getValue());
        }
        return {name: config.title, fields: fieldValues};
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


    function handleMoveRequest(srcSectionIndex, srcFieldIndex, destSectionIndex, destFieldIndex) {
        if (onMoveRequest) {
            onMoveRequest(srcSectionIndex, srcFieldIndex, destSectionIndex, destFieldIndex);
        }
    }


</script>

<div role="group" class="card mb-3"
     ondragover={(e) => {
       e.preventDefault();
       e.dataTransfer.dropEffect = "move";
     }}
     ondrop={(e) =>{
       e.preventDefault();
       e.stopPropagation();
       const moveSource = JSON.parse(e.dataTransfer.getData("application/json"));
       onMoveRequest(moveSource.section, moveSource.field, sectionIndex, -1);
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
                            {#each sectionTypes as sectionType (sectionType.value)}
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
                />
            </div>
        {/each}

        {#if editable}

            <div class="d-flex justify-content-between">
                <button class="btn btn-primary" onclick={addField}><i class="bx bx-plus"></i> Add field</button>
                <div></div>
                <button class="btn btn-danger" onclick={() => {onDeleteSectionRequest()}}><i class="bx bxs-trash"></i>
                    Delete section
                </button>
            </div>

        {/if}
    </div>
</div>


