<script lang="ts">
  import {getUniqueID} from "../../misc.svelte.js";
  import {TextType} from "../../interfaces.ts";

  let {config, value = $bindable(), viewerMode = false} = $props();

  let componentId = getUniqueID();
  let isValid = $state(false);
  let isInvalid = $state(false);
  let validationErrorFeedback = $state("The field must not be empty.");

  function setIsValid(valid) {
    isValid = valid;
    isInvalid = !valid;
  }

  function validateEmail(email: string){
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  }

  export function validate() {
    // If not required then value always validates
    if (!config.required)
      return true;

    // Check for empty field
    if (value === null || value === undefined || value.length < 1) {
      validationErrorFeedback = "The field must not be empty";
      setIsValid(false)
      return false
    }

    // Check for number
    if (config.textType === TextType.integer || config.textType === TextType.decimals) {
        console.log("Validating numbers");
      if (isNaN(Number(value))) {
        validationErrorFeedback = "Invalid number entered."
        setIsValid(false)
        return false
      }
      else{
          console.log("Success", Number(value));
      }
    }

    // Check for email
    if (config.textType === TextType.email) {
        console.log("Validating email address");
        if(!validateEmail(value)){
            validationErrorFeedback = "Please enter a valid email."
            setIsValid(false)
            return false
        }
        else{
            console.log("Email validation success");
        }
    }

    // Check for max char length
    if (config.enforceValueConstraints) {
      // Enforce max char length for plaintext
      if (config.textType === TextType.plain && value.length > config.maxNumChar) {
        validationErrorFeedback = "You've exceeded the maximum character limit of "+config.maxNumChar +", current length is "+value.length+".";
        setIsValid(false)
        return false
      }

      // Enforce integer value range
      if (config.textType === TextType.integer) {
        let numValue = parseInt(value);
        if (numValue < parseInt(config.minNumValue) || numValue > parseInt(config.maxNumValue)) {
          validationErrorFeedback = "Number must be in the range of "+config.minNumValue+ " to "+config.maxNumValue+".";
          setIsValid(false)
          return false
        }
      }

      // Enforce float value range
      if (config.textType === TextType.decimals) {
        let numValue = parseFloat(value);
        if (numValue < parseFloat(config.minNumValue) || numValue > parseFloat(config.maxNumValue)) {
          validationErrorFeedback = "Number must be in the range of "+config.minNumValue+ " to "+config.maxNumValue+".";
          setIsValid(false)
          return false
        }
      }

    }

    setIsValid(true);
    return true;
  }

</script>
<div class="col-12">
    <label class="form-label" for={componentId}>{config.label}{#if config.required}<span style="color: red">*</span>{/if}</label>
    {#if config.description || config.description.length > 0}<p class="form-text">{config.description}</p>{/if}
    <input type="text"
           class={{"form-control": true,"is-valid": isValid, "is-invalid": isInvalid}}
           bind:value={value}
           required={config.required}
           id={componentId}
           disabled={viewerMode}
    >
    <span class="invalid-feedback">
        {validationErrorFeedback}
    </span>
</div>
