<script lang="ts" module>
    let currentEditor;

    export function getDefaultFieldConfig() {
        return {
            type: "text",
            name: "question_name",
            label: "New Question",
            description: "Question description",
            required: true,
            sublabels: [],
            options: [],
        };
    }
</script>
<script lang="ts">
    import Text from "./Text.svelte";
    import TextArea from "./TextArea.svelte";
    import Checkbox from "./Checkbox.svelte";
    import Radio from "./Radio.svelte";
    import Select from "./Select.svelte"
    import Likert from "./Likert.svelte";
    import OptionsList from "./OptionsList.svelte";

    //Constants
    const questionTypes = [
        {label: "Text", value: "text"},
        {label: "Textarea", value: "textarea"},
        {label: "Radio", value: "radio"},
        {label: "Checkbox", value: "checkbox"},
        {label: "Selector", value: "select"},
        {label: "Likert", value: "likert"},
    ]
    const renderComponentTypes = {
        text: Text,
        textarea: TextArea,
        radio: Radio,
        checkbox: Checkbox,
        select: Select,
        likert: Likert
    }
    const componentTypeWithOptions = new Set(["radio", "checkbox", "select", "likert"]);
    const componentTypeWithSublabels = new Set(["likert"]);

    // Props
    let {
        config = $bindable(getDefaultFieldConfig()),
        editable = false,
        value = $bindable(),
        onEditRequest = (startEdit: boolean) => {
        },
        onDuplicateRequest = () => {
        },
        onDeleteRequest = () => {
        },
    } = $props();

    //Insert missing keys
    let defultConfig = getDefaultFieldConfig()
    for(let key in defultConfig){
        if(!(key in config)){
            config[key] = defultConfig[key];
        }
    }

    // States
    let inEditMode = $state(false);




    let RenderedComponentType = $derived.by(() => {
        if (config.type in renderComponentTypes) {
            return renderComponentTypes[config.type];
        }
        return Text;
    })

    export function validate() {
        console.log("Validating field" + config.name);
    }

    export function getValue(){
        return {name: config.name, value: value};
    }

    export function beginEdit() {
        inEditMode = true;
    }

    export function endEdit() {
        inEditMode = false;
    }



</script>

<div>
{#if editable && inEditMode}

    <div class="card mb-3" >
        <div class="card-header" style="text-align: right">
            <button onclick={()=>{onEditRequest(false)}} class="btn btn-link btn-sm" aria-label="Close">
                <i class='bx bx-radio-circle-marked'></i>
                <i class='bx bx-collapse-vertical'></i> close
            </button>
        </div>
        <div class="card-body">

            <div class="row mb-3">
                <div class="col-8">
                    <label class="form-label col-12">
                        Question label
                        <input type="text" class="form-control" bind:value={config.label} />
                    </label>
                </div>
                <div class="col-4">
                    <label class="form-label col-12">
                        Question type
                        <select bind:value={config.type} class="form-select">
                            {#each questionTypes as questionType}
                                <option value={questionType.value}>{questionType.label} </option>
                            {/each}
                        </select>
                    </label>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label col-12">
                    Question name
                    <input type="text" class="form-control" bind:value={config.name}/>
                </label>
            </div>

            <div class="mb-3">
                <label class="form-label col-12">
                    Description
                    <textarea class="form-control" bind:value={config.description} ></textarea>
                </label>
            </div>

            {#if componentTypeWithSublabels.has(config.type)}
                <div class="mb-3">
                    <label class="form-label">Sublabels</label>
                    <OptionsList bind:options={config.sublabels} type={config.type}/>
                </div>
            {/if}

            {#if componentTypeWithOptions.has(config.type)}
                <div class="mb-3">
                    <label class="form-label">Options</label>
                    <OptionsList bind:options={config.options} type={config.type}/>

                </div>
            {/if}

            <div class="form-check form-switch mb-3">
                <label class="form-label">
                    Required
                    <input type="checkbox" class="form-check-input" role="switch" bind:checked={config.required}/>
                </label>
            </div>

            <div>
                <button class="btn btn-primary" onclick={() => {onDuplicateRequest()}}>Duplicate</button>
                <button class="btn btn-danger" onclick={() => {onDeleteRequest()}}>Delete</button>
            </div>


        </div>
    </div>

{:else if editable && !inEditMode}
    <a href="/" class="card mb-3 sort-form-component" onclick={(event)=>{event.preventDefault(); onEditRequest(true)}}>
        <div class="card-body">
            <label class="form-label col-12">
                {config.label}
                {#if config.required}<span style="color: red">*</span>{/if}
                <RenderedComponentType config={config}></RenderedComponentType>
            </label>
        </div>
    </a>
{:else}

    <label class="form-label col-12">
        {config.label}
        {#if config.required}<span style="color: red">*</span>{/if}
        <RenderedComponentType config={config} bind:value={value}></RenderedComponentType>
    </label>

{/if}
</div>

<style>
    .sort-form-component:hover {
        background: #cec3fa;
    }

</style>
