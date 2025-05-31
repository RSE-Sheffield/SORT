<script lang="ts">
  import DOMPurify  from "dompurify";
  import {getUniqueID} from "../../misc.svelte.ts";
  let {config, value = $bindable(), viewerMode = false} = $props();



  let componentId = getUniqueID();
  let isValid = $state(false);
  let isInvalid = $state(false);

  function setIsValid(valid) {
    isValid = valid;
    isInvalid = !valid;
  }

  export function validate() {
    // Always true as the selector will always pick the first option
    return true;
  }


</script>
<div class="col-12">
    <label class="form-label" for={componentId}>{config.label}{#if config.required}<span style="color: red">*</span>{/if}</label>
    {#if config.description || config.description.length > 0}<p class="form-text">{@html DOMPurify.sanitize(config.description)}</p>{/if}
    <select class={{"form-select": true,"is-valid": isValid, "is-invalid": isInvalid}}
            bind:value={value}
            required={config.required}
            id={componentId}
            disabled={viewerMode}
    >
        {#each config.options as option (option)}
            <option value={option}>{option}</option>
        {/each}
    </select>
    <div class="invalid-feedback">
        An item must be selected.
    </div>
</div>

