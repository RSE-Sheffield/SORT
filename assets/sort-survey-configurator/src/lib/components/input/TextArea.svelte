<script>
  import {getUniqueID} from "../../misc.svelte.ts";
  let {config, value = $bindable()} = $props();

  let componentId = getUniqueID();
  let isValid = $state(false);
  let isInvalid = $state(false);
  let validationErrorFeedback = $state("The field must not be empty.");

  function setIsValid(valid) {
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
    <label class="form-label" for={componentId}>{config.label}</label>
    {#if config.required}<span style="color: red">*</span>{/if}
    <textarea class={{"form-control": true,"is-valid": isValid, "is-invalid": isInvalid}}
              bind:value={value}
              required={config.required}
              id={componentId}
    ></textarea>
    <span class="invalid-feedback">
        {validationErrorFeedback}
    </span>
</div>


