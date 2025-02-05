<script>
  let {config, value = $bindable()} = $props();
</script>

<input type="text" class="form-control" name={config.name} bind:value={value}>

