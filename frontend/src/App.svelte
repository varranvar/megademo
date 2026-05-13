<script>
  import ToolRegistry from './lib/ToolRegistry.js'
  import DataLoader from './lib/DataLoader.js'
  import BugTriage from './components/BugTriage.svelte'
  import CveAudit from './components/CveAudit.svelte'
  import GenericTool from './components/GenericTool.svelte'

  let tools = []
  let selectedTool = null
  let selectedRun = null
  let runData = null

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

<main>
  <h1>Package Analyser</h1>
  <p class="subtitle">Canonical Hackathon — Read-only analysis suite</p>

  <div class="layout">
    <aside>
      <h2>Tools</h2>
      {#each tools as tool}
        <div class="tool-section">
          <h3>{tool.name}</h3>
          <ul>
            {#each tool.runs as run}
              <li>
                <button onclick={() => loadRun(tool.name, run)}>
                  {run}
                </button>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
      {#if tools.length === 0}
        <p class="empty">No analysis data yet.</p>
      {/if}
    </aside>

    <section class="viewer">
      {#if runData}
        <h2>{selectedTool} — {selectedRun}</h2>
        {#if selectedTool === 'bug-triage'}
          <BugTriage data={runData} />
        {:else if selectedTool === 'cve-audit'}
          <CveAudit data={runData} />
        {:else}
          <GenericTool data={runData} />
        {/if}
      {:else}
        <p class="placeholder">Select a run from the sidebar to view analysis results.</p>
      {/if}
    </section>
  </div>
</main>

<style>
  .subtitle {
    color: #666;
    margin-top: -1rem;
    margin-bottom: 2rem;
  }
  .layout {
    display: flex;
    gap: 2rem;
    text-align: left;
  }
  aside {
    min-width: 250px;
    border-right: 1px solid #ccc;
    padding-right: 1rem;
  }
  .tool-section h3 {
    margin-bottom: 0.5rem;
    text-transform: capitalize;
  }
  .tool-section ul {
    list-style: none;
    padding: 0;
    margin: 0 0 1.5rem 0;
  }
  .tool-section li {
    margin-bottom: 0.25rem;
  }
  button {
    background: none;
    border: none;
    color: #0074d9;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    font-size: inherit;
  }
  button:hover {
    color: #0056a6;
  }
  .viewer {
    flex: 1;
  }
  .empty, .placeholder {
    color: #888;
    font-style: italic;
  }
</style>
