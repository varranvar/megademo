const DATA_ROOT = ''

const KNOWN_TOOLS = [
  'bug-triage',
  'cve-audit',
  'vulnerability-analysis',
  'autopkgtest-recommendations',
]

async function loadManifest(toolName) {
  try {
    const resp = await fetch(`${DATA_ROOT}/${toolName}/manifest.json`)
    if (!resp.ok) return []
    return await resp.json()
  } catch (e) {
    return []
  }
}

export default {
  async list() {
    const results = []
    for (const name of KNOWN_TOOLS) {
      const runs = await loadManifest(name)
      if (runs.length > 0) {
        results.push({ name, runs })
      }
    }
    return results
  }
}
