# Agent Instructions

## Skill directory

All skills for this project live in **`.agents/skills/`** at the repository root. This is the single shared location used by everyone on the team, regardless of which AI tool or model you're using.

- **Creating a new skill**: write it to `.agents/skills/<skill-name>/SKILL.md`
- **Editing a skill**: edit it in-place under `.agents/skills/<skill-name>/`
- **Never** create skills in `/tmp`, session workspaces, or any other location

Each skill follows the structure:
```
.agents/skills/<skill-name>/
├── SKILL.md            ← required: YAML frontmatter + instructions
├── scripts/            ← optional: helper scripts
├── references/         ← optional: supporting docs
└── assets/             ← optional: templates, icons, fonts
```

For the full skill authoring workflow (drafting, testing, evaluating, iterating), invoke the **skill-creator** skill located at `.agents/skills/skill-creator/`.
