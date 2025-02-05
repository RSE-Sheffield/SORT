<script lang="ts" module>
    export function getDefaultSectionConfig(){
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
    import * as _ from "lodash"
    import InputComponent, {getDefaultFieldConfig} from "./InputComponent.svelte";
    import EditableText from "./EditableText.svelte";
    import EditableTextArea from "./EditableTextArea.svelte";


    let {
        config = $bindable(getDefaultSectionConfig()),
        editable = false,
        sectionTypeEditable = true,
        displaySectionType=true,
        value = $bindable(),
        onEditRequest = (fieldIndex: number, doEdit: boolean) => {
        }
    } = $props();

    //Insert missing keys
    let defultConfig = getDefaultSectionConfig()
    for(let key in defultConfig){
        if(!(key in config)){
            config[key] = defultConfig[key];
        }
    }

    // Keeps track of all field components
    let _fieldComponents = $state([])
    let fieldComponents = $derived(_fieldComponents.filter(Boolean));


    let fieldValues = $state(value !== null && value !== undefined ? value :[]);
    $effect(()=>{
       value = _.cloneDeep(fieldValues);
    });

    let textVal = $state();


    export function validate() {
        console.log("Validating section");
        for (let i in fieldComponents) {
            fieldComponents[i].validate();
        }
    }

    export function getValue(){
        let fieldValues = []
        for (let i = 0; i < fieldComponents.length; i++) {
            fieldValues.push(fieldComponents[i].getValue());
        }
        return { name: config.title, fields: fieldValues};
    }

    export function stopEditingAll() {
        for (let i = 0; i < fieldComponents.length; i++) {
            fieldComponents[i].endEdit();
        }
    }

    export function startEditAtIndex(fieldIndex) {
        for (let i = 0; i < fieldComponents.length; i++) {
            if(i == fieldIndex){
                fieldComponents[fieldIndex].beginEdit();
            }
            else{
                fieldComponents[i].endEdit();
            }

        }

    }

    function addField() {
        config.fields.push(getDefaultFieldConfig())
    }

    function duplicateField(index: number) {
        config.fields.splice(index, 0, _.cloneDeep(config.fields[index]));
    }

    function deleteField(index: number) {
        config.fields.splice(index, 1);
    }


</script>

<div class="card mb-3">
    <div class="card-body">
        <div class="row">
            <div class="col-8">
                <h2>
                {#if editable}
                    <EditableText bind:value={config.title}/>
                {:else}
                    {config.title}
                {/if}
                </h2>
            </div>
            <div class="col-4 text-end">
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
                        {config.description}
                    {/if}
                </p>
            </div>


        </div>


        {#each config.fields as field, index (index)}
            <div class="mb-3">
                <InputComponent
                        bind:config={config.fields[index]}
                        editable={editable}
                        onEditRequest={(startEdit)=>{onEditRequest(index, startEdit)}}
                        onDuplicateRequest={()=>{duplicateField(index)}}
                        onDeleteRequest={()=>{deleteField(index)}}
                        bind:value={fieldValues[index]}
                        bind:this={_fieldComponents[index]}
                />
            </div>
        {/each}

        {#if editable}
            <button class="btn btn-primary" onclick={addField}>Add field</button>
        {/if}
    </div>
</div>
