<script>
  let {config, value = $bindable()} = $props();
</script>

<select class="form-select" name={config.name} bind:value={value}>
    {#each config.options as option}
        <option value={option}>{option}</option>
    {/each}
</select>


