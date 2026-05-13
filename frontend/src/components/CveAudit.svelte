<script>
  let { data } = $props()

  let cves = $derived(data.cves || [])
  let seriesSummary = $derived(data.series_summary || {})
  let prioritySummary = $derived(data.priority_summary || {})
  let versions = $derived(data.current_versions || {})
</script>

{#if Object.keys(seriesSummary).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Series Risk Summary</h3>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Series</th>
                <th class="center">Open</th>
                <th class="center">Needs Eval</th>
                <th class="center">Fixed</th>
                <th class="center">Not Affected</th>
                <th class="center">Other</th>
              </tr>
            </thead>
            <tbody>
              {#each Object.entries(seriesSummary) as [seriesName, stats]}
                <tr>
                  <td class="series-name">{seriesName}</td>
                  <td class="center {stats.open > 0 ? 'danger' : ''}">{stats.open || 0}</td>
                  <td class="center">{stats.needs_evaluation || 0}</td>
                  <td class="center safe">{stats.fixed || 0}</td>
                  <td class="center">{stats.not_affected || 0}</td>
                  <td class="center">{stats.other || 0}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
{/if}

{#if prioritySummary && Object.keys(prioritySummary).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Priority Summary</h3>
        <div class="priority-badges">
          {#each ['Critical', 'High', 'Medium', 'Low', 'Negligible'] as prio}
            {#if prioritySummary[prio] > 0}
              <span class="priority-badge priority-{prio.toLowerCase()}">
                {prio}: <strong>{prioritySummary[prio]}</strong>
              </span>
            {/if}
          {/each}
        </div>
      </div>
    </div>
  </section>
{/if}

{#if versions && !versions.error && Object.keys(versions).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Current Versions</h3>
        <div class="version-grid">
          {#each Object.entries(versions) as [seriesName, info]}
            <div class="version-item">
              <span class="version-series">{info.display_name || seriesName}</span>
              <span class="version-number">{info.version || 'N/A'}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </section>
{/if}

{#if cves.length > 0}
  <section>
    <h3>CVEs ({data.cves_analyzed} of {data.total_cves_found})</h3>
    <div class="cve-grid">
      {#each cves as cve}
        <div class="p-card cve-card">
          <div class="cve-header">
            <span class="cve-id">{cve.cve_id}</span>
            <span class="priority-badge priority-{cve.priority?.toLowerCase() || 'unknown'}">
              {cve.priority || 'Unknown'}
            </span>
          </div>
          <div class="cve-body">
            <p class="cve-status">{cve.summary_status}</p>
            <p class="cve-desc">{cve.description}</p>
            {#if cve.package_statuses && Object.keys(cve.package_statuses).length > 0}
              <div class="status-table-wrapper">
                <table class="status-table">
                  <tbody>
                    {#each Object.entries(Object.values(cve.package_statuses)[0]) as [s, status]}
                      <tr>
                        <td>{s}</td>
                        <td class="{status.toLowerCase().includes('vulnerable') ? 'danger' : status.toLowerCase().includes('fixed') ? 'safe' : ''}">
                          {status}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </section>
{:else if data.package}
  <section>
    <div class="p-notification--warning p-notification">
      <div class="p-notification__content">
        <p class="p-notification__message">No CVEs found for <strong>{data.package}</strong>.</p>
      </div>
    </div>
  </section>
{/if}

<style>
  section {
    margin: 0 0 1.5rem 0;
  }

  h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: #2c2c2c;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid #eee;
  }

  th {
    background: #fafafa;
    font-weight: 500;
    color: #666;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .center {
    text-align: center;
  }

  .series-name {
    font-weight: 500;
  }

  .danger {
    color: #c7162b;
    font-weight: 600;
    background: rgba(199, 22, 43, 0.08);
  }

  .safe {
    color: #0e8420;
  }

  .priority-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .priority-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 100px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .priority-critical { background: rgba(199, 22, 43, 0.12); color: #c7162b; }
  .priority-high { background: rgba(233, 84, 32, 0.12); color: #c34113; }
  .priority-medium { background: rgba(249, 155, 17, 0.15); color: #b87a0d; }
  .priority-low { background: rgba(14, 132, 32, 0.12); color: #0e8420; }
  .priority-negligible { background: rgba(153, 153, 153, 0.15); color: #666; }
  .priority-unknown { background: rgba(102, 102, 102, 0.15); color: #444; }

  .version-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .version-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .version-series {
    font-size: 0.8rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .version-number {
    font-weight: 600;
    color: #2c2c2c;
    font-family: monospace;
    font-size: 0.9rem;
  }

  .cve-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.25rem;
  }

  .cve-card {
    margin: 0;
  }

  .cve-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background: #fafafa;
    border-bottom: 1px solid #eee;
  }

  .cve-id {
    font-weight: 600;
    font-size: 1rem;
    color: #2c2c2c;
  }

  .cve-body {
    padding: 1rem 1.25rem;
  }

  .cve-status {
    color: #888;
    font-size: 0.85rem;
    margin: 0 0 0.5rem 0;
  }

  .cve-desc {
    font-size: 0.9rem;
    color: #444;
    margin: 0 0 0.75rem 0;
    line-height: 1.5;
  }

  .status-table-wrapper {
    margin-top: 0.75rem;
  }

  .status-table {
    width: 100%;
    font-size: 0.85rem;
  }

  .status-table td {
    padding: 0.5rem 0.75rem;
    border: none;
  }

  .status-table td:first-child {
    color: #888;
    width: 40%;
  }

  .status-table td:last-child {
    font-weight: 500;
  }
</style>
