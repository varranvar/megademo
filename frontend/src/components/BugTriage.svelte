<script>
  let { data } = $props()
</script>

{#if data.summary}
  <div class="p-card u-no-padding--top">
    <h3 class="p-heading--5">Summary</h3>
    <ul class="p-list">
      <li class="p-list__item">Similar Launchpad bugs: <strong>{data.summary.total_similar_lp_bugs}</strong></li>
      <li class="p-list__item">Upstream issues: <strong>{data.summary.total_upstream_issues}</strong></li>
      <li class="p-list__item">Upstream found: <strong>{data.summary.upstream_found ? 'Yes' : 'No'}</strong></li>
    </ul>
  </div>
{/if}

{#if data.input_bug}
  <div class="p-card">
    <h3 class="p-heading--5">Input Bug #{data.input_bug.id}</h3>
    <p class="p-text--default"><strong>{data.input_bug.title}</strong></p>
    <p class="p-text--small">Status: {data.input_bug.status} | Importance: {data.input_bug.importance}</p>
    <p class="p-text--small">Package: {data.input_bug.package_name || 'N/A'}</p>
    <p><a class="p-button--positive is-dense" href={data.input_bug.web_link} target="_blank">View on Launchpad</a></p>
  </div>
{/if}

{#if data.similar_launchpad_bugs && data.similar_launchpad_bugs.length > 0}
  <h3 class="p-heading--5">Similar Launchpad Bugs</h3>
  <div class="bug-list">
    {#each data.similar_launchpad_bugs as bug}
      <div class="p-card">
        <p class="p-text--default"><strong>#{bug.id}</strong> — {bug.title}</p>
        <p class="p-text--small">Status: {bug.status} | Importance: {bug.importance}</p>
        <p><a href={bug.web_link} target="_blank">View</a></p>
      </div>
    {/each}
  </div>
{/if}

{#if data.upstream_issues && data.upstream_issues.length > 0}
  <h3 class="p-heading--5">Upstream Issues</h3>
  <div class="bug-list">
    {#each data.upstream_issues as issue}
      <div class="p-card">
        <p class="p-text--default"><strong>{issue.title}</strong> ({issue.source})</p>
        <p class="p-text--small">State: {issue.state}</p>
        <p><a href={issue.url} target="_blank">View</a></p>
      </div>
    {/each}
  </div>
{/if}

<style>
  .bug-list {
    display: grid;
    gap: 1rem;
    margin-bottom: 1rem;
  }
</style>
