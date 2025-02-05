<script>
  let {config, value = $bindable()} = $props();
</script>

<textarea class="form-control" name={config.name} bind:value={value}></textarea>


