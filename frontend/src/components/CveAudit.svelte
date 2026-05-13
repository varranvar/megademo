<script>
  let { data } = $props()

  let cves = $derived(data.cves || [])
  let series = $derived(data.supported_series || [])
  let versions = $derived(data.current_versions || {})
  let seriesSummary = $derived(data.series_summary || {})
  let prioritySummary = $derived(data.priority_summary || {})
</script>

{#if Object.keys(seriesSummary).length > 0}
  <div class="p-card u-no-padding--bottom">
    <h3 class="p-heading--4">Series Risk Summary</h3>
    <table class="p-table--mobile-card" role="grid">
      <thead>
        <tr>
          <th scope="col">Series</th>
          <th scope="col">Open</th>
          <th scope="col">Needs Eval</th>
          <th scope="col">Fixed</th>
          <th scope="col">Not Affected</th>
          <th scope="col">Other</th>
        </tr>
      </thead>
      <tbody>
        {#each Object.entries(seriesSummary) as [seriesName, stats]}
          <tr>
            <td aria-label="Series">{seriesName}</td>
            <td aria-label="Open" class={stats.open > 0 ? 'p-text--error' : 'p-text--success'}>{stats.open}</td>
            <td aria-label="Needs Eval">{stats.needs_evaluation}</td>
            <td aria-label="Fixed">{stats.fixed}</td>
            <td aria-label="Not Affected">{stats.not_affected}</td>
            <td aria-label="Other">{stats.other}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

{#if prioritySummary && Object.keys(prioritySummary).length > 0}
  <div class="p-card">
    <h3 class="p-heading--4">Priority Summary</h3>
    <div class="p-chip-group">
      {#each Object.entries(prioritySummary) as [prio, count]}
        {#if count > 0}
          <span class="p-chip--{prio.toLowerCase()}">{prio}: {count}</span>
        {/if}
      {/each}
    </div>
  </div>
{/if}

{#if versions && !versions.error}
  <div class="p-card">
    <h3 class="p-heading--4">Current Versions</h3>
    <ul class="p-list">
      {#each Object.entries(versions) as [seriesName, info]}
        <li class="p-list__item"><strong>{info.display_name || seriesName}:</strong> {info.version || 'N/A'}</li>
      {/each}
    </ul>
  </div>
{/if}

{#if cves.length > 0}
  <h3 class="p-heading--4">CVEs ({data.cves_analyzed} of {data.total_cves_found})</h3>
  <div class="row">
    {#each cves as cve}
      <div class="col-6">
        <div class="p-card">
          <div class="p-card__header">
            <h4 class="p-heading--5">{cve.cve_id}</h4>
            <span class="p-status-label--{cve.priority.toLowerCase()}">{cve.priority}</span>
          </div>
          <hr />
          <div class="p-card__content">
            <p class="u-text--muted">{cve.summary_status}</p>
            <p class="p-text--small">{cve.description}</p>
            {#if cve.package_statuses && Object.keys(cve.package_statuses).length > 0}
              <table class="p-table--mobile-card">
                <thead>
                  <tr>
                    <th scope="col">Series</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {#each Object.entries(Object.values(cve.package_statuses)[0]) as [s, status]}
                    <tr>
                      <td aria-label="Series">{s}</td>
                      <td aria-label="Status" class={
                        status.toLowerCase().includes('vulnerable') ? 'p-text--error' :
                        status.toLowerCase().includes('fixed') || status.toLowerCase().includes('released') ? 'p-text--success' :
                        ''
                      }>{status}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>
{:else}
  <div class="p-notification--warning">
    <div class="p-notification__content">
      <h5 class="p-notification__title">No CVEs Found</h5>
      <p class="p-notification__message">No CVEs found for <strong>{data.package}</strong> in the analysed pages.</p>
    </div>
  </div>
{/if}

<style>
  .p-chip-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
</style>
