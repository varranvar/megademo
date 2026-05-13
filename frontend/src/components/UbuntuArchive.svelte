<script>
  let { data } = $props()

  let summary = $derived(data.summary || {})
  let versions = $derived(data.versions || {})
  let buildStatus = $derived(data.build_status || {})
  let autopkgtestResults = $derived(data.autopkgtest_results || {})
  let reverseDeps = $derived(data.reverse_dependencies || {})
  let bugs = $derived(data.bugs || [])
  let packageDetails = $derived(data.package_details || {})

  function importanceClass(importance) {
    const map = { 'Critical': 'p-status-label--critical', 'High': 'p-status-label--high', 'Medium': 'p-status-label--medium', 'Low': 'p-status-label--low', 'Wishlist': 'p-status-label--negligible', 'Undecided': 'p-status-label--unknown' }
    return map[importance] || 'p-status-label--unknown'
  }

  function buildStatusClass(status) {
    if (status.includes('Successfully')) return 'build-success'
    if (status.includes('Failed')) return 'build-failed'
    if (status.includes('building') || status.includes('progress')) return 'build-progress'
    return ''
  }

  function adtStatusClass(status) {
    if (status === 'pass') return 'adt-pass'
    if (status === 'fail') return 'adt-fail'
    return ''
  }
</script>

{#if summary && Object.keys(summary).length > 0}
  <section class="summary-section">
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-number">{summary.series_count}</div>
        <div class="summary-label">Series</div>
      </div>
      <div class="summary-card">
        <div class="summary-number {summary.builds_failed > 0 ? 'warning' : 'success'}">{summary.builds_succeeded}/{summary.architectures_built}</div>
        <div class="summary-label">Builds OK</div>
      </div>
      <div class="summary-card">
        <div class="summary-number {summary.autopkgtest_fail > 0 ? 'warning' : 'success'}">{summary.autopkgtest_pass}/{summary.autopkgtest_pass + summary.autopkgtest_fail}</div>
        <div class="summary-label">Tests Pass</div>
      </div>
      <div class="summary-card">
        <div class="summary-number">{summary.reverse_dep_count}</div>
        <div class="summary-label">Reverse Deps</div>
      </div>
      <div class="summary-card">
        <div class="summary-number {summary.critical_bugs > 0 ? 'danger' : ''}">{summary.open_bugs}</div>
        <div class="summary-label">Open Bugs</div>
      </div>
    </div>
  </section>
{/if}

{#if versions && Object.keys(versions).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Versions Across Series</h3>
        <div class="version-grid">
          {#each Object.entries(versions) as [seriesName, version]}
            <div class="version-item">
              <span class="version-series">{seriesName}</span>
              <span class="version-number">{version}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </section>
{/if}

{#if packageDetails && packageDetails.data}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Package Details</h3>
        <div class="details-grid">
          {#if packageDetails.data.Package}
            <div class="detail-item">
              <span class="detail-label">Package</span>
              <span class="detail-value">{packageDetails.data.Package}</span>
            </div>
          {/if}
          {#if packageDetails.data.Version}
            <div class="detail-item">
              <span class="detail-label">Version</span>
              <span class="detail-value detail-mono">{packageDetails.data.Version}</span>
            </div>
          {/if}
          {#if packageDetails.data.Section}
            <div class="detail-item">
              <span class="detail-label">Section</span>
              <span class="detail-value">{packageDetails.data.Section}</span>
            </div>
          {/if}
          {#if packageDetails.data.Priority}
            <div class="detail-item">
              <span class="detail-label">Priority</span>
              <span class="detail-value">{packageDetails.data.Priority}</span>
            </div>
          {/if}
          {#if packageDetails.data.Maintainer}
            <div class="detail-item detail-wide">
              <span class="detail-label">Maintainer</span>
              <span class="detail-value">{packageDetails.data.Maintainer}</span>
            </div>
          {/if}
          {#if packageDetails.data.Description}
            <div class="detail-item detail-wide">
              <span class="detail-label">Description</span>
              <span class="detail-value">{packageDetails.data.Description}</span>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </section>
{/if}

{#if buildStatus && Object.keys(buildStatus).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Build Status</h3>
        {#each Object.entries(buildStatus) as [seriesName, builds]}
          <div class="build-series">
            <h4>{seriesName}</h4>
            <div class="build-grid">
              {#each builds as build}
                <div class="build-card {buildStatusClass(build.status)}">
                  <span class="build-arch">{build.arch}</span>
                  <span class="build-status">{build.status}</span>
                  {#if build.duration}
                    <span class="build-duration">{build.duration}</span>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>
{/if}

{#if autopkgtestResults && Object.keys(autopkgtestResults).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Autopkgtest Results</h3>
        {#each Object.entries(autopkgtestResults) as [seriesName, results]}
          <div class="adt-series">
            <h4>{seriesName}</h4>
            <div class="adt-grid">
              {#each results as result}
                <div class="adt-card {adtStatusClass(result.status)}">
                  <span class="adt-arch">{result.arch}</span>
                  <span class="adt-status">{result.status}</span>
                  <span class="adt-version">{result.version}</span>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>
{/if}

{#if reverseDeps && Object.keys(reverseDeps).length > 0}
  <section>
    <div class="p-card">
      <div class="p-card__content">
        <h3>Reverse Dependencies</h3>
        {#each Object.entries(reverseDeps) as [seriesName, depTypes]}
          <div class="rdep-series">
            <h4>{seriesName}</h4>
            {#each Object.entries(depTypes) as [depType, packages]}
              <div class="rdep-group">
                <span class="rdep-type">{depType}</span>
                <div class="rdep-chips">
                  {#each packages as pkg}
                    <span class="rdep-chip">{pkg}</span>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        {/each}
      </div>
    </div>
  </section>
{/if}

{#if bugs && bugs.length > 0}
  <section>
    <h3>Open Bugs ({bugs.length})</h3>
    <div class="bug-grid">
      {#each bugs as bug}
        <div class="p-card bug-card">
          <div class="p-card__header">
            <a href={bug.url} target="_blank" rel="noopener noreferrer" class="bug-id">
              #{bug.id}
            </a>
            <span class="p-status-label {importanceClass(bug.importance)}">{bug.importance}</span>
          </div>
          <div class="p-card__content">
            <p class="bug-title-small">{bug.title}</p>
            <div class="bug-meta-small">
              <span class="p-status-label">{bug.status}</span>
              {#if bug.assignee}
                <span class="bug-assignee">Assigned: {bug.assignee}</span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
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

  h4 {
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0 0 0.75rem 0;
    color: #444;
  }

  .summary-section {
    margin: 0 0 1.5rem 0;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
  }

  .summary-card {
    background: #fff;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .summary-number {
    font-size: 1.75rem;
    font-weight: 600;
    color: #2c2c2c;
    line-height: 1.2;
  }

  .summary-number.success {
    color: #0e8420;
  }

  .summary-number.warning {
    color: #f99b11;
  }

  .summary-number.danger {
    color: #c7162b;
  }

  .summary-label {
    color: #666;
    font-size: 0.8rem;
    margin-top: 0.25rem;
  }

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

  .details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0.75rem;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .detail-item.detail-wide {
    grid-column: 1 / -1;
  }

  .detail-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .detail-value {
    font-weight: 500;
    color: #2c2c2c;
    font-size: 0.9rem;
    line-height: 1.4;
  }

  .detail-mono {
    font-family: monospace;
  }

  .build-series {
    margin-bottom: 1.25rem;
  }

  .build-series:last-child {
    margin-bottom: 0;
  }

  .build-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.75rem;
  }

  .build-card {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    border: 1px solid #eee;
    background: #fafafa;
  }

  .build-card.build-success {
    border-color: rgba(14, 132, 32, 0.3);
    background: rgba(14, 132, 32, 0.05);
  }

  .build-card.build-failed {
    border-color: rgba(199, 22, 43, 0.3);
    background: rgba(199, 22, 43, 0.05);
  }

  .build-card.build-progress {
    border-color: rgba(249, 155, 17, 0.3);
    background: rgba(249, 155, 17, 0.05);
  }

  .build-arch {
    font-weight: 600;
    font-size: 0.85rem;
    color: #2c2c2c;
  }

  .build-status {
    font-size: 0.8rem;
    color: #555;
  }

  .build-success .build-status {
    color: #0e8420;
    font-weight: 500;
  }

  .build-failed .build-status {
    color: #c7162b;
    font-weight: 500;
  }

  .build-progress .build-status {
    color: #b87a0d;
    font-weight: 500;
  }

  .build-duration {
    font-size: 0.75rem;
    color: #888;
  }

  .adt-series {
    margin-bottom: 1.25rem;
  }

  .adt-series:last-child {
    margin-bottom: 0;
  }

  .adt-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 0.75rem;
  }

  .adt-card {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.6rem 0.9rem;
    border-radius: 6px;
    border: 1px solid #eee;
    background: #fafafa;
  }

  .adt-card.adt-pass {
    border-color: rgba(14, 132, 32, 0.3);
    background: rgba(14, 132, 32, 0.05);
  }

  .adt-card.adt-fail {
    border-color: rgba(199, 22, 43, 0.3);
    background: rgba(199, 22, 43, 0.05);
  }

  .adt-arch {
    font-weight: 600;
    font-size: 0.85rem;
    color: #2c2c2c;
  }

  .adt-status {
    font-size: 0.8rem;
    text-transform: capitalize;
  }

  .adt-pass .adt-status {
    color: #0e8420;
    font-weight: 500;
  }

  .adt-fail .adt-status {
    color: #c7162b;
    font-weight: 500;
  }

  .adt-version {
    font-size: 0.7rem;
    color: #888;
    font-family: monospace;
  }

  .rdep-series {
    margin-bottom: 1.25rem;
  }

  .rdep-series:last-child {
    margin-bottom: 0;
  }

  .rdep-group {
    margin-bottom: 0.75rem;
  }

  .rdep-type {
    display: inline-block;
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 0.35rem;
  }

  .rdep-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }

  .rdep-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.65rem;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
    background: rgba(233, 84, 32, 0.08);
    color: #c34113;
  }

  .bug-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 1rem;
  }

  .bug-card {
    margin: 0;
  }

  .bug-id {
    color: #e95420;
    font-weight: 600;
    text-decoration: none;
    font-size: 1rem;
  }

  .bug-id:hover {
    text-decoration: underline;
  }

  .bug-title-small {
    margin: 0 0 0.5rem 0;
    font-weight: 500;
    color: #2c2c2c;
    font-size: 0.9rem;
    line-height: 1.4;
  }

  .bug-meta-small {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    font-size: 0.8rem;
  }

  .bug-assignee {
    color: #888;
  }
</style>
