<script>
  export let data
</script>

{#if data.summary}
  <div class="summary">
    <h3>Summary</h3>
    <ul>
      <li>Similar Launchpad bugs: {data.summary.total_similar_lp_bugs}</li>
      <li>Upstream issues: {data.summary.total_upstream_issues}</li>
      <li>Upstream found: {data.summary.upstream_found ? 'Yes' : 'No'}</li>
    </ul>
  </div>
{/if}

{#if data.input_bug}
  <div class="bug-card">
    <h3>Input Bug #{data.input_bug.id}</h3>
    <p><strong>{data.input_bug.title}</strong></p>
    <p>Status: {data.input_bug.status} | Importance: {data.input_bug.importance}</p>
    <p>Package: {data.input_bug.package_name || 'N/A'}</p>
    <p><a href={data.input_bug.web_link} target="_blank">View on Launchpad</a></p>
  </div>
{/if}

{#if data.similar_launchpad_bugs && data.similar_launchpad_bugs.length > 0}
  <h3>Similar Launchpad Bugs</h3>
  <div class="bug-list">
    {#each data.similar_launchpad_bugs as bug}
      <div class="bug-card">
        <p><strong>#{bug.id}</strong> — {bug.title}</p>
        <p>Status: {bug.status} | Importance: {bug.importance}</p>
        <p><a href={bug.web_link} target="_blank">View</a></p>
      </div>
    {/each}
  </div>
{/if}

{#if data.upstream_issues && data.upstream_issues.length > 0}
  <h3>Upstream Issues</h3>
  <div class="bug-list">
    {#each data.upstream_issues as issue}
      <div class="bug-card">
        <p><strong>{issue.title}</strong> ({issue.source})</p>
        <p>State: {issue.state}</p>
        <p><a href={issue.url} target="_blank">View</a></p>
      </div>
    {/each}
  </div>
{/if}

<style>
  .summary {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  .bug-card {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  .bug-list {
    display: grid;
    gap: 0.5rem;
  }
  a {
    color: #0074d9;
  }
</style>
