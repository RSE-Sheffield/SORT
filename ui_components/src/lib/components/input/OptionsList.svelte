<script lang="ts">
  import type {FieldType} from "../../interfaces.ts";

  interface Props {
    options: string[];
    type: FieldType|null;
    readonly : boolean;
    hasOtherOption?: boolean;

  }
    let {options = $bindable(), type = null, readonly=false, hasOtherOption = $bindable()}: Props = $props();

    function addOption(){
        options.push("Option " + (options.length + 1));
    }

    function deleteOption(index){
        options.splice(index, 1);
    }

    function setHasOtherOption(hasOption: boolean){
      hasOtherOption = hasOption;
    }



    /**
     * Handle pasting text into an option text input.
     */
    function handlePaste(event, index) {
        // Get the pasted text
        const pastedText = event.clipboardData.getData("text");

        // If the pasted text is multiline, process it to generate new options.
        // Otherwise, just paste it into field as normal.
        if (pastedText.includes("\n")) {
            // Prevent the default paste behavior
            event.preventDefault();

            // Split the text into lines and remove whitespace
            const lines = pastedText.split('\n').map(line => line.trim())
                .filter(line => line.length > 0); // Remove empty lines

            if (lines.length >= 1) {
                // Replace the current option with the first line
                options[index] = lines[0];

                // Insert the remaining lines as new options after the current one
                const newOptions = lines.slice(1);
                options.splice(index + 1, 0, ...newOptions);
            }
        }
    }
</script>
{#each options as option, index (index)}
<div class="input-group mb-1">
    <!-- Icon (based on question type) -->
     <span class="input-group-text">
         {#if type === "radio"}
            <i class='bx bx-radio-circle-marked' ></i>
         {:else if type === "checkbox"}
             <i class='bx bx-check-square' ></i>
         {:else if type === "select"}
             <i class='bx bx-menu' ></i>
         {:else if type === "likert"}
             <i class='bx bxs-grid'></i>
         {/if}
     </span>
     <input class="form-control" type="text" bind:value={options[index]} readonly={readonly}
       onpaste={readonly ? undefined : (e) => handlePaste(e, index)} />
    {#if readonly}
    <button class="btn btn-outline-secondary" aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {:else}
    <button class="btn btn-outline-danger" onclick={()=>{deleteOption(index)}} aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {/if}
</div>
{/each}
{#if type === "radio" && hasOtherOption}
<div class="input-group mb-1">
    <!-- Icon (based on question type) -->
     <span class="input-group-text">
         {#if type === "radio"}
            <i class='bx bx-radio-circle-marked' ></i>
         {:else if type === "checkbox"}
             <i class='bx bx-check-square' ></i>
         {:else if type === "select"}
             <i class='bx bx-menu' ></i>
         {:else if type === "likert"}
             <i class='bx bxs-grid'></i>
         {/if}
     </span>
    <span class="input-group-text">
        "Other"
    </span>
     <input class="form-control" type="text" value="" readonly={true}/>
    {#if readonly}
    <button class="btn btn-outline-secondary" aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {:else}
    <button class="btn btn-outline-danger" onclick={()=>{setHasOtherOption(false)}} aria-label="Delete option" title="Delete option"><i class='bx bx-x' ></i></button>
    {/if}
</div>
{/if}
<div>
    {#if readonly}
    <button class="btn btn-secondary btn-sm"><i class="bx bx-plus"></i> Add option</button>
    {:else}
    <button class="btn btn-primary btn-sm" onclick={addOption}><i class="bx bx-plus"></i> Add option</button>
        {#if type === "radio" && !hasOtherOption}
            or <button class="btn btn-primary btn-sm" onclick={()=>{setHasOtherOption(true)}}><i class="bx bx-plus"></i> Add "Other" option</button>
        {/if}
    {/if}
</div>
