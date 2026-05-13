const DATA_ROOT = ''

export default {
  async load(toolName, runId) {
    const resp = await fetch(`${DATA_ROOT}/${toolName}/${runId}`)
    if (!resp.ok) {
      throw new Error(`Failed to load ${toolName}/${runId}: ${resp.status}`)
    }
    return await resp.json()
  }
}
