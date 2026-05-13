<script>
  export let data

  $: cves = data.cves || []
  $: series = data.supported_series || []
  $: versions = data.current_versions || {}
  $: seriesSummary = data.series_summary || {}
  $: prioritySummary = data.priority_summary || {}
</script>

{#if Object.keys(seriesSummary).length > 0}
  <div class="summary">
    <h3>Series Risk Summary</h3>
    <table class="risk-table">
      <thead>
        <tr>
          <th>Series</th>
          <th>Open</th>
          <th>Needs Eval</th>
          <th>Fixed</th>
          <th>Not Affected</th>
          <th>Other</th>
        </tr>
      </thead>
      <tbody>
        {#each Object.entries(seriesSummary) as [seriesName, stats]}
          <tr>
            <td>{seriesName}</td>
            <td class={stats.open > 0 ? 'warning' : 'ok'}>{stats.open}</td>
            <td>{stats.needs_evaluation}</td>
            <td>{stats.fixed}</td>
            <td>{stats.not_affected}</td>
            <td>{stats.other}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

{#if prioritySummary}
  <div class="summary">
    <h3>Priority Summary</h3>
    <ul class="priority-list">
      {#each Object.entries(prioritySummary) as [prio, count]}
        {#if count > 0}
          <li><span class="badge badge-{prio}">{prio}</span> {count}</li>
        {/if}
      {/each}
    </ul>
  </div>
{/if}

{#if versions && !versions.error}
  <div class="versions">
    <h3>Current Versions</h3>
    <ul>
      {#each Object.entries(versions) as [seriesName, info]}
        <li><strong>{info.display_name || seriesName}:</strong> {info.version || 'N/A'}</li>
      {/each}
    </ul>
  </div>
{/if}

{#if cves.length > 0}
  <h3>CVEs ({data.cves_analyzed} of {data.total_cves_found})</h3>
  <div class="cve-list">
    {#each cves as cve}
      <div class="cve-card">
        <div class="cve-header">
          <h4>{cve.cve_id}</h4>
          <span class="priority priority-{cve.priority.toLowerCase()}">{cve.priority}</span>
          <span class="status">{cve.summary_status}</span>
        </div>
        <p class="description">{cve.description}</p>
        {#if cve.package_statuses && Object.keys(cve.package_statuses).length > 0}
          <table class="status-table">
            <thead>
              <tr>
                <th>Series</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {#each Object.entries(Object.values(cve.package_statuses)[0]) as [s, status]}
                <tr>
                  <td>{s}</td>
                  <td class={
                    status.toLowerCase().includes('vulnerable') ? 'warning' :
                    status.toLowerCase().includes('fixed') || status.toLowerCase().includes('released') ? 'ok' :
                    ''
                  }>{status}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    {/each}
  </div>
{:else}
  <p class="empty">No CVEs found for <strong>{data.package}</strong> in the analysed pages.</p>
{/if}

<style>
  .summary {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  .versions {
    background: #eef;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  .risk-table, .status-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.5rem;
  }
  th, td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
  }
  .warning {
    color: #d32f2f;
    font-weight: bold;
  }
  .ok {
    color: #388e3c;
  }
  .cve-list {
    display: grid;
    gap: 1rem;
  }
  .cve-card {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
  }
  .cve-header {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }
  .priority {
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.875rem;
    text-transform: uppercase;
    font-weight: bold;
  }
  .priority-critical { background: #d32f2f; color: white; }
  .priority-high { background: #f57c00; color: white; }
  .priority-medium { background: #fbc02d; color: black; }
  .priority-low { background: #388e3c; color: white; }
  .priority-negligible { background: #9e9e9e; color: white; }
  .priority-unknown { background: #ccc; color: black; }
  .status {
    color: #666;
    font-size: 0.9rem;
  }
  .description {
    color: #444;
    margin-bottom: 0.75rem;
  }
  .priority-list {
    list-style: none;
    padding: 0;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .badge {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    text-transform: uppercase;
    font-weight: bold;
  }
  .badge-critical { background: #d32f2f; color: white; }
  .badge-high { background: #f57c00; color: white; }
  .badge-medium { background: #fbc02d; color: black; }
  .badge-low { background: #388e3c; color: white; }
  .badge-negligible { background: #9e9e9e; color: white; }
  .badge-unknown { background: #ccc; color: black; }
  .empty {
    color: #888;
    font-style: italic;
  }
</style>
