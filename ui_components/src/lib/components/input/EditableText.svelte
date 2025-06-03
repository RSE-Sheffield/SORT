<script lang="ts">
    interface Props {
        value: string,
        placeholder?: string
    }

    let {value = $bindable(""), placeholder = "Enter text here"}: Props = $props();


</script>

<input class="focus-ring" bind:value={value} style="border:none; border-radius: 0.12em; width: 100%" placeholder="Enter text here"/>


