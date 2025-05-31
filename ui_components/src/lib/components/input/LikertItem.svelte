<script>

  let {config, sublabelIndex, value = $bindable(), viewerMode=false} = $props();

  let isValid = $state(false);
  let isInvalid = $state(false);

  function setIsValid(valid) {
    isValid = valid;
    isInvalid = !valid;
  }

  export function validate() {
    if (config.required && !value) {
      setIsValid(false);
      return false;
    }

    setIsValid(true);
    return true;
  }
</script>

<div class={{
  "bg-light": sublabelIndex % 2 < 1,
  "pb-3": true,
  "pt-3": true,
  "ps-2": true,
  "pe-2": true}} 
     style="border-bottom: black 1px">

    <div class="row mb-2">
        <div class="col">
            <span class={{"is-valid": isValid, "is-invalid": isInvalid}}>{config.sublabels[sublabelIndex]}</span>
            <span class="invalid-feedback">A value must be selected</span>
        </div>
    </div>
    <div class="row">
        {#each config.options as option (option)}
            <div class="col">
                <div class="form-check">
                    <label class="form-check-label">
                        {option}
                        <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                               type="radio"
                               value={option}
                               bind:group={value}
                               required={config.required}
                               disabled={viewerMode}
                        /></label>
                </div>
            </div>
        {/each}
    </div>

</div>


