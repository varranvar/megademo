<script>
  import ToolRegistry from './lib/ToolRegistry.js'
  import DataLoader from './lib/DataLoader.js'
  import BugTriage from './components/BugTriage.svelte'
  import CveAudit from './components/CveAudit.svelte'
  import GenericTool from './components/GenericTool.svelte'

  let tools = $state([])
  let selectedTool = $state(null)
  let selectedRun = $state(null)
  let runData = $state(null)
  let loading = $state(false)
  let error = $state(null)

  async function refreshTools() {
    loading = true
    error = null
    try {
      tools = await ToolRegistry.list()
    } catch (e) {
      error = 'Failed to load tools'
    }
    loading = false
  }

  refreshTools()

  async function loadRun(tool, runId) {
    loading = true
    error = null
    try {
      selectedTool = tool
      selectedRun = runId
      runData = await DataLoader.load(tool, runId)
    } catch (e) {
      error = `Failed to load ${tool}/${runId}: ${e.message}`
      runData = null
    }
    loading = false
  }
</script>

<div class="l-application" style="min-height: 100vh;">
  <header class="l-navigation-bar">
    <div class="p-panel is-dark">
      <div class="p-panel__header">
        <h1 class="p-panel__title">
          <img src="https://assets.ubuntu.com/v1/2f631679-ubuntu-logo-white-bg.svg" alt="Ubuntu" style="height: 1.5rem; margin-right: 0.5rem; vertical-align: middle;" />
          Package Analyser
        </h1>
        <div class="p-panel__controls">
          <span class="p-label--floating">Canonical Hackathon</span>
        </div>
      </div>
    </div>
  </header>

  <aside class="l-navigation">
    <div class="p-panel">
      <div class="p-panel__content">
        <h5 class="p-heading--5 u-sv1">Analysis Tools</h5>
        <nav>
          {#each tools as tool}
            <div class="u-sv1">
              <h6 class="p-text--small-caps">{tool.name}</h6>
              <ul class="p-list--divided">
                {#each tool.runs as run}
                  <li class="p-list__item">
                    <button 
                      class="p-button--base is-dense is-wide {selectedTool === tool.name && selectedRun === run ? 'is-active' : ''}" 
                      onclick={() => loadRun(tool.name, run)}
                    >
                      <span class="p-text--small">{run}</span>
                    </button>
                  </li>
                {/each}
              </ul>
            </div>
          {/each}
          {#if tools.length === 0 && !loading}
            <p class="p-text--small u-text--muted">No analysis data yet.</p>
          {/if}
        </nav>
      </div>
    </div>
  </aside>

  <main class="l-main">
    <div class="p-strip is-shallow">
      <div class="u-fixed-width">
        {#if loading}
          <div class="p-notification--information">
            <div class="p-notification__content">
              <p class="p-notification__message">
                <i class="p-icon--spinner u-animation--spin"></i>
                Loading...
              </p>
            </div>
          </div>
        {:else if error}
          <div class="p-notification--negative">
            <div class="p-notification__content">
              <h5 class="p-notification__title">Error</h5>
              <p class="p-notification__message">{error}</p>
            </div>
          </div>
        {:else if runData}
          <div class="u-sv1">
            <h2 class="p-heading--3">{selectedTool}</h2>
            <p class="p-text--muted">{selectedRun}</p>
          </div>
          <hr class="u-sv1" />
          {#if selectedTool === 'bug-triage'}
            <BugTriage data={runData} />
          {:else if selectedTool === 'cve-audit'}
            <CveAudit data={runData} />
          {:else}
            <GenericTool data={runData} />
          {/if}
        {:else}
          <div class="p-strip is-narrow">
            <div class="u-fixed-width">
              <div class="p-notification--information">
                <div class="p-notification__content">
                  <h5 class="p-notification__title">Welcome to Package Analyser</h5>
                  <p class="p-notification__message">
                    This tool provides AI-powered analysis of Ubuntu Archive packages.
                    Select a run from the sidebar to view analysis results.
                  </p>
                </div>
              </div>
              <div class="row u-sv3">
                <div class="col-4">
                  <div class="p-card">
                    <h4 class="p-card__title">Bug Triage</h4>
                    <p class="p-card__content">Find duplicate bugs and upstream issues for Ubuntu packages.</p>
                  </div>
                </div>
                <div class="col-4">
                  <div class="p-card">
                    <h4 class="p-card__title">CVE Audit</h4>
                    <p class="p-card__content">Analyse CVEs affecting packages across Ubuntu series.</p>
                  </div>
                </div>
                <div class="col-4">
                  <div class="p-card">
                    <h4 class="p-card__title">More Tools</h4>
                    <p class="p-card__content">Lintian fixes, coverage analysis, and more coming soon.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </main>
</div>

<style>
  .is-wide {
    width: 100%;
    text-align: left;
  }
  
  .is-active {
    background-color: var(--color-surface-selected);
    border-left: 3px solid var(--color-accent);
  }
</style>
