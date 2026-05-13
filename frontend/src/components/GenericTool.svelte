<script>
  let { data } = $props()
</script>

<div class="p-card">
  <pre>{JSON.stringify(data, null, 2)}</pre>
</div>

<style>
  pre {
    text-align: left;
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 1rem;
    border-radius: 0.25rem;
    overflow-x: auto;
    margin: 0;
  }
</style>
