<script lang="ts">
    import SectionComponent from "./input/SectionComponent.svelte";
    let {config, response} = $props();
</script>
{#each config.sections as sectionConfig, index}
    <SectionComponent config={sectionConfig} value={response[index]} editable={false} viewerMode={true}/>
{/each}
