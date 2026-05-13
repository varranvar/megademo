<script>
  let { data } = $props()
</script>

{#if data.summary}
  <div class="p-strip is-shallow">
    <div class="u-fixed-width">
      <div class="p-card u-no-padding--bottom">
        <h3 class="p-heading--4">Summary</h3>
        <div class="row">
          <div class="col-4">
            <div class="p-card--highlighted">
              <p class="p-heading--2">{data.summary.total_similar_lp_bugs}</p>
              <p class="p-text--muted">Similar Launchpad Bugs</p>
            </div>
          </div>
          <div class="col-4">
            <div class="p-card--highlighted">
              <p class="p-heading--2">{data.summary.total_upstream_issues}</p>
              <p class="p-text--muted">Upstream Issues</p>
            </div>
          </div>
          <div class="col-4">
            <div class="p-card--highlighted">
              <p class="p-heading--2">{data.summary.upstream_found ? 'Yes' : 'No'}</p>
              <p class="p-text--muted">Upstream Found</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if data.input_bug}
  <div class="u-fixed-width u-sv1">
    <div class="p-card">
      <div class="p-card__header">
        <h4 class="p-card__title">Input Bug #{data.input_bug.id}</h4>
      </div>
      <hr />
      <div class="p-card__content">
        <h5 class="p-heading--5">{data.input_bug.title}</h5>
        <div class="row u-sv1">
          <div class="col-3">
            <p class="p-text--muted">Status</p>
            <p><span class="p-status-label">{data.input_bug.status}</span></p>
          </div>
          <div class="col-3">
            <p class="p-text--muted">Importance</p>
            <p><span class="p-status-label--information">{data.input_bug.importance}</span></p>
          </div>
          <div class="col-3">
            <p class="p-text--muted">Package</p>
            <p>{data.input_bug.package_name || 'N/A'}</p>
          </div>
          <div class="col-3">
            <p class="p-text--muted">Heat</p>
            <p>{data.input_bug.heat || 0}</p>
          </div>
        </div>
        <a class="p-button--positive is-dense" href={data.input_bug.web_link} target="_blank" rel="noopener noreferrer">
          <i class="p-icon--external-link"></i>&nbsp;View on Launchpad
        </a>
      </div>
    </div>
  </div>
{/if}

{#if data.similar_launchpad_bugs && data.similar_launchpad_bugs.length > 0}
  <div class="u-fixed-width u-sv1">
    <h3 class="p-heading--4">Similar Launchpad Bugs ({data.similar_launchpad_bugs.length})</h3>
    <div class="row">
      {#each data.similar_launchpad_bugs as bug}
        <div class="col-6">
          <div class="p-card">
            <div class="p-card__header">
              <h5 class="p-heading--5">
                <a href={bug.web_link} target="_blank" rel="noopener noreferrer">#{bug.id}</a>
              </h5>
              <span class="p-status-label">{bug.status}</span>
            </div>
            <hr />
            <div class="p-card__content">
              <p class="p-text--default">{bug.title}</p>
              <p class="p-text--small u-text--muted">
                {bug.importance} importance | Heat: {bug.heat}
              </p>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

{#if data.upstream_issues && data.upstream_issues.length > 0}
  <div class="u-fixed-width u-sv1">
    <h3 class="p-heading--4">Upstream Issues ({data.upstream_issues.length})</h3>
    <div class="row">
      {#each data.upstream_issues as issue}
        <div class="col-6">
          <div class="p-card">
            <div class="p-card__header">
              <h5 class="p-heading--5">{issue.title}</h5>
              <span class="p-label--floating">{issue.source}</span>
            </div>
            <hr />
            <div class="p-card__content">
              <p class="p-text--small">
                <span class="p-status-label--{issue.state === 'open' ? 'error' : 'success'}">{issue.state}</span>
              </p>
              {#if issue.url}
                <a href={issue.url} target="_blank" rel="noopener noreferrer" class="p-button--base is-dense">
                  View Issue
                </a>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}
