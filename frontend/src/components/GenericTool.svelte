<script>
  let { data } = $props()
</script>

<div class="p-card">
  <div class="p-card__header">
    <h4 class="p-heading--4">Raw Data</h4>
  </div>
  <hr />
  <div class="p-card__content">
    <pre class="p-code-copyable"><code>{JSON.stringify(data, null, 2)}</code></pre>
  </div>
</div>
