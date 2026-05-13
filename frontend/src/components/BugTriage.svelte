<script>
  let { data } = $props()
</script>

{#if data.summary}
  <section class="summary-section">
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-number">{data.summary.total_similar_lp_bugs}</div>
        <div class="summary-label">Similar Bugs</div>
      </div>
      <div class="summary-card">
        <div class="summary-number">{data.summary.total_upstream_issues}</div>
        <div class="summary-label">Upstream Issues</div>
      </div>
      <div class="summary-card">
        <div class="summary-number {data.summary.upstream_found ? 'success' : 'warning'}">
          {data.summary.upstream_found ? 'Found' : 'Not Found'}
        </div>
        <div class="summary-label">Upstream</div>
      </div>
    </div>
  </section>
{/if}

{#if data.input_bug}
  <section>
    <div class="p-card">
      <div class="p-card__header">
        <h3>Input Bug #{data.input_bug.id}</h3>
        <span class="p-status-label">{data.input_bug.status}</span>
      </div>
      <div class="p-card__content">
        <h4 class="bug-title">{data.input_bug.title}</h4>
        
        <div class="bug-meta">
          <div class="meta-item">
            <span class="meta-label">Importance</span>
            <span class="p-status-label p-status-label--medium">{data.input_bug.importance}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Package</span>
            <span class="meta-value">{data.input_bug.package_name || 'N/A'}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Heat</span>
            <span class="meta-value">{data.input_bug.heat || 0}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Created</span>
            <span class="meta-value">{new Date(data.input_bug.date_created).toLocaleDateString()}</span>
          </div>
        </div>

        <a class="launchpad-link" href={data.input_bug.web_link} target="_blank" rel="noopener noreferrer">
          View on Launchpad →
        </a>
      </div>
    </div>
  </section>
{/if}

{#if data.similar_launchpad_bugs && data.similar_launchpad_bugs.length > 0}
  <section>
    <h3>Similar Launchpad Bugs ({data.similar_launchpad_bugs.length})</h3>
    <div class="bug-grid">
      {#each data.similar_launchpad_bugs as bug}
        <div class="p-card bug-card">
          <div class="p-card__header">
            <a href={bug.web_link} target="_blank" rel="noopener noreferrer" class="bug-id">
              #{bug.id}
            </a>
            <span class="p-status-label">{bug.status}</span>
          </div>
          <div class="p-card__content">
            <p class="bug-title-small">{bug.title}</p>
            <div class="bug-meta-small">
              <span>{bug.importance}</span>
              <span>•</span>
              <span>Heat: {bug.heat}</span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </section>
{/if}

{#if data.upstream_issues && data.upstream_issues.length > 0}
  <section>
    <h3>Upstream Issues ({data.upstream_issues.length})</h3>
    <div class="bug-grid">
      {#each data.upstream_issues as issue}
        <div class="p-card bug-card">
          <div class="p-card__header">
            <span class="issue-source">{issue.source}</span>
            <span class="p-status-label {issue.state === 'open' ? 'p-status-label--critical' : 'p-status-label--low'}">
              {issue.state}
            </span>
          </div>
          <div class="p-card__content">
            <p class="bug-title-small">{issue.title}</p>
            {#if issue.url}
              <a href={issue.url} target="_blank" rel="noopener noreferrer" class="launchpad-link">
                View Issue →
              </a>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </section>
{/if}

<style>
  .summary-section {
    margin: 0 0 1.5rem 0;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1.5rem;
  }

  .summary-card {
    background: #fff;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .summary-number {
    font-size: 2.25rem;
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

  .summary-label {
    color: #666;
    font-size: 0.85rem;
    margin-top: 0.25rem;
  }

  .bug-title {
    font-size: 1.15rem;
    font-weight: 500;
    margin: 0 0 1rem 0;
    color: #2c2c2c;
  }

  .bug-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
    margin-bottom: 1.25rem;
  }

  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .meta-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .meta-value {
    font-weight: 500;
    color: #2c2c2c;
  }

  .launchpad-link {
    display: inline-block;
    color: #e95420;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
  }

  .launchpad-link:hover {
    text-decoration: underline;
  }

  .bug-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
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
    font-size: 0.95rem;
  }

  .bug-meta-small {
    display: flex;
    gap: 0.5rem;
    color: #888;
    font-size: 0.85rem;
  }

  .issue-source {
    background: #f5f5f5;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #666;
  }

  section {
    margin: 0 0 1.5rem 0;
  }

  h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    color: #2c2c2c;
  }
</style>
