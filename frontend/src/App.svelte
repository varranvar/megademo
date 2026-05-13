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

  function parseRunName(runId) {
    const match = runId.match(/^(.+)-(\d{4}-\d{2}-\d{2})\.json$/)
    if (match) {
      return { package: match[1], date: match[2] }
    }
    return { package: runId.replace(/\.json$/, ''), date: null }
  }

  async function refreshTools() {
    loading = true
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

<div class="l-application">
  <header class="l-navigation-bar">
    <div class="p-panel is-dark">
      <div class="p-panel__header">
        <h1 class="p-panel__title">
          <img 
            src="https://assets.ubuntu.com/v1/2f631679-ubuntu-logo-white-bg.svg" 
            alt="" 
            height="28"
          />
          <span>Package Analyser</span>
        </h1>
        <div class="p-panel__controls">
          <span class="p-label">Canonical Hackathon</span>
        </div>
      </div>
    </div>
  </header>

  <aside class="l-navigation">
    <div class="p-panel">
      <div class="p-panel__content">
        <h5>Analysis Tools</h5>
        <nav>
          {#each tools as tool}
            <section>
              <h6>{tool.name}</h6>
              <ul class="p-list--divided">
                {#each tool.runs as run}
                  {@const parsed = parseRunName(run)}
                  <li class="p-list__item">
                    <button 
                      class="is-wide {selectedTool === tool.name && selectedRun === run ? 'is-active' : ''}" 
                      onclick={() => loadRun(tool.name, run)}
                    >
                      <span class="run-package">{parsed.package}</span>
                      {#if parsed.date}
                        <span class="run-date">{parsed.date}</span>
                      {/if}
                    </button>
                  </li>
                {/each}
              </ul>
            </section>
          {/each}
          {#if tools.length === 0 && !loading}
            <p class="u-text--muted">No analysis data available.</p>
          {/if}
        </nav>
      </div>
    </div>
  </aside>

  <main class="l-main">
    {#if loading}
      <div class="p-notification--information p-notification">
        <div class="p-notification__content">
          <p class="p-notification__message">
            <span class="u-animation--spin">⟳</span> Loading...
          </p>
        </div>
      </div>
    {:else if error}
      <div class="p-notification--negative p-notification">
        <div class="p-notification__content">
          <h5 class="p-notification__title">Error</h5>
          <p class="p-notification__message">{error}</p>
        </div>
      </div>
    {:else if runData}
      {@const parsed = parseRunName(selectedRun)}
      <h2>{parsed.package}</h2>
      {#if parsed.date}
        <p class="run-date-header">{parsed.date}</p>
      {/if}
      {#if selectedTool === 'bug-triage'}
        <BugTriage data={runData} />
      {:else if selectedTool === 'cve-audit'}
        <CveAudit data={runData} />
      {:else}
        <GenericTool data={runData} />
      {/if}
    {:else}
      <div class="welcome-section">
        <div class="p-notification--information p-notification">
          <div class="p-notification__content">
            <h5 class="p-notification__title">Welcome to Package Analyser</h5>
            <p class="p-notification__message">
              AI-powered analysis for Ubuntu Archive packages. Select a run from the sidebar to view results.
            </p>
          </div>
        </div>

        <div class="feature-grid">
          <div class="p-card">
            <div class="p-card__content">
              <h4>Bug Triage</h4>
              <p>Find duplicate bugs and upstream issues for Ubuntu packages.</p>
            </div>
          </div>
          <div class="p-card">
            <div class="p-card__content">
              <h4>CVE Audit</h4>
              <p>Analyse CVEs affecting packages across Ubuntu series.</p>
            </div>
          </div>
          <div class="p-card">
            <div class="p-card__content">
              <h4>More Tools</h4>
              <p>Lintian fixes, coverage analysis, and more coming soon.</p>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .is-wide {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }
  
  .is-active {
    background-color: rgba(233, 84, 32, 0.1);
    border-left: 3px solid #e95420;
    margin-left: -3px;
    font-weight: 500;
  }

  .run-package {
    color: #2c2c2c;
  }

  .run-date {
    color: #999;
    font-size: 0.8rem;
  }

  h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #2c2c2c;
    padding-top: 1rem;
  }

  .run-date-header {
    margin: 0.25rem 0 0.75rem 0;
    color: #999;
    font-size: 0.9rem;
  }

  .welcome-section {
    max-width: 900px;
    padding-top: 1rem;
  }

  .welcome-section .p-notification {
    margin: 0;
  }

  .feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
  }

  .feature-grid .p-card {
    margin: 0;
  }

  .feature-grid h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
  }

  .feature-grid p {
    margin: 0;
    color: #666;
    font-size: 0.9rem;
  }
</style>
