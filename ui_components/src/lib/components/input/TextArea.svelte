<script lang="ts">
  import {getUniqueID} from "../../misc.svelte.ts";
  let {config, value = $bindable(), viewerMode = false} = $props();
  import DOMPurify from "dompurify";

  // Ensure value is always a string when bound
  // If there's undefined then the value passed up is missing, rather
  // than null or an empty string, which corrupts the data structure.
  $effect(() => {
    if (value === undefined || value === null) {
      value = "";
    }
  });

  let componentId = getUniqueID();
  let isValid = $state(false);
  let isInvalid = $state(false);
  let validationErrorFeedback = $state("The field must not be empty.");

  function setIsValid(valid: boolean) {
    isValid = valid;
    isInvalid = !valid;
  }

  export function validate() {

    // If not required then value always validates
    if(!config.required)
      return true;

    // Check for empty field
    if(value === null || value === undefined || value.length < 1){
      validationErrorFeedback = "The field must not be empty";
      setIsValid(false)
      return false
    }

    // Check for max char length
    if(config.enforceValueConstraints && value.length > config.maxNumChar){
      validationErrorFeedback = "You've exceeded the maximum character limit of "+config.maxNumChar +", current length is "+value.length+".";
      setIsValid(false)
      return false
    }

    setIsValid(true);
    return true;
  }

</script>
<div class="col-12">
    <label class="form-label" for={componentId}>{config.label}{#if config.required}<span style="color: red">*</span>{/if}</label>
    {#if config.description || config.description.length > 0}<p class="form-text">{@html DOMPurify.sanitize(config.description)}</p>{/if}
    <textarea class={{"form-control": true,"is-valid": isValid, "is-invalid": isInvalid}}
              bind:value={value}
              required={config.required}
              id={componentId}
              disabled={viewerMode}
    ></textarea>
    <span class="invalid-feedback">
        {validationErrorFeedback}
    </span>
</div>


