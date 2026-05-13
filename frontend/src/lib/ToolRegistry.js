const DATA_ROOT = ''

const KNOWN_TOOLS = [
  'bug-triage',
  'cve-audit',
  'ubuntu-archive',
  'exploiter',
  'vulnerability-analysis',
  'autopkgtest-recommendations',
]

async function loadManifest(toolName) {
  try {
    const resp = await fetch(`${DATA_ROOT}/${toolName}/manifest.json`)
    if (!resp.ok) return []
    const data = await resp.json()
    return data.map(entry => typeof entry === 'string' ? entry : entry.file)
  } catch (e) {
    return []
  }
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
