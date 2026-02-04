<script lang="ts">
import PellEditor from "./PellEditor.svelte";

let {value = $bindable("") } = $props();

</script>
<PellEditor bind:value={value}  ></PellEditor>


