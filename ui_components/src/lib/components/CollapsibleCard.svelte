<script lang="ts">

    import {getUniqueID} from "../misc.svelte.ts";
    import {slide} from "svelte/transition"
    import type {Snippet} from "svelte";

    interface Props {
        title: string,
        content?: Snippet,
        startCollapsed?: boolean
    }

    let {title = "Collapsible content", content, startCollapsed = false}: Props = $props();

    const collapseHeaderId = getUniqueID();
    const collapseContentId = getUniqueID();

    let collapseContent: HTMLElement = $state();
    let collapse = $state(startCollapsed);

    function toggleCollapse(e) {
        e.preventDefault();
        collapse = !collapse;
    }
</script>
<div class="card">
    <div class="card-header" id={collapseHeaderId}>
        <a onclick={toggleCollapse}
           href="#"
           data-target="#{collapseContentId}"
           aria-expanded="true"
           aria-controls={collapseContentId}
           style="text-decoration: none; color: inherit"
        >
            <div class="d-flex justify-content-between">
                <div class="me-3">
                    <span style="font-weight: bold">{title}</span>
                </div>
                <button class="btn-primary btn">
                    {#if collapse}
                        <i class='bx bx-expand-vertical'></i> Expand
                    {:else}
                        <i class='bx bx-collapse-vertical' ></i> Collapse
                    {/if}
                </button>
            </div>

        </a>
    </div>

    {#if !collapse}
        <div bind:this={collapseContent}
             id={collapseContentId}
             class="card-body"
             aria-labelledby={collapseHeaderId}
             transition:slide
        >
            {@render content?.()}
        </div>
    {/if}
</div>
