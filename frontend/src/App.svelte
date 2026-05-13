<script>
  import ToolRegistry from './lib/ToolRegistry.js'
  import DataLoader from './lib/DataLoader.js'
  import BugTriage from './components/BugTriage.svelte'
  import CveAudit from './components/CveAudit.svelte'
  import Exploiter from './components/Exploiter.svelte'
  import GenericTool from './components/GenericTool.svelte'

  let tools = $state([])
  let selectedTool = $state(null)
  let selectedRun = $state(null)
  let runData = $state(null)

  async function refreshTools() {
    tools = await ToolRegistry.list()
  }

  refreshTools()

  async function loadRun(tool, runId) {
    selectedTool = tool
    selectedRun = runId
    runData = await DataLoader.load(tool, runId)
  }
</script>

<div class="l-application">
  <header class="l-navigation-bar">
    <div class="p-panel is-dark">
      <div class="p-panel__header">
        <h4 class="p-panel__title">Package Analyser</h4>
        <div class="p-panel__controls">
          <span class="p-text--small">Canonical Hackathon</span>
        </div>
      </div>
    </div>
  </header>

  <aside class="l-navigation">
    <div class="p-panel">
      <div class="p-panel__content">
        <h5 class="p-text--small-caps">Tools</h5>
        <nav>
          {#each tools as tool}
            <div class="tool-section u-no-margin--bottom">
              <h6 class="p-text--small-caps">{tool.name}</h6>
              <ul class="p-list--divided">
                {#each tool.runs as run}
                  <li class="p-list__item">
                    <button class="p-button--base is-dense u-no-margin--bottom" onclick={() => loadRun(tool.name, run)}>
                      {run}
                    </button>
                  </li>
                {/each}
              </ul>
            </div>
          {/each}
          {#if tools.length === 0}
            <p class="p-text--small u-text--muted">No analysis data yet.</p>
          {/if}
        </nav>
      </div>
    </div>
  </aside>

  <main class="l-main">
    <div class="p-strip is-shallow">
      <div class="u-fixed-width">
        {#if runData}
          <h2 class="p-heading--4">{selectedTool} — {selectedRun}</h2>
          {#if selectedTool === 'bug-triage'}
            <BugTriage data={runData} />
          {:else if selectedTool === 'cve-audit'}
            <CveAudit data={runData} />
          {:else if selectedTool === 'exploiter'}
            <Exploiter data={runData} />
          {:else}
            <GenericTool data={runData} />
          {/if}
        {:else}
          <div class="p-notification--information">
            <div class="p-notification__content">
              <h5 class="p-notification__title">Welcome</h5>
              <p class="p-notification__message">Select a run from the sidebar to view analysis results.</p>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </main>
</div>
