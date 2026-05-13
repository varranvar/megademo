---
name: launchpad-query
description: Query Launchpad for information about Ubuntu projects, bugs, packages, people, Git repositories, CVEs, snap recipes, and more. Use this skill whenever the user wants to look up Launchpad bugs, search for Ubuntu packages, find project info, look up a Launchpad person or team, search for Git repositories on Launchpad, look up CVEs, check snap build status, browse blueprints/specs, or interact with any Launchpad.net resource. Also use when the user mentions Launchpad, LP bugs, Ubuntu package versions, PPA info, merge proposals, or wants to search for any resource hosted on launchpad.net.
---

# Launchpad Query

Use the `lpcli` command-line tool (`/home/karl.smeltzer@canonical.com/.cargo/bin/lpcli`) to query Launchpad.net from the terminal.

## Available commands

Run `lpcli <COMMAND>` with one of the following subcommands:

| Command | What it does |
|---------|-------------|
| `bug` | Query and manage Launchpad bugs |
| `person` | Query people and teams |
| `package` | Query Ubuntu packages and distro series |
| `project` | Query Launchpad projects |
| `cve` | Look up CVEs |
| `git` | Query Git repositories |
| `snap` | Query Snap recipes |
| `spec` | Query specifications (blueprints) |
| `question` | Query Launchpad questions/answers |
| `webhook` | Manage webhooks |
| `translation` | Query translations |
| `access-token` | Manage personal access tokens |
| `status` | Check authentication status |

## Bug queries (`lpcli bug`)

- **Show a bug**: `lpcli bug show <bug-id>` — bug-id can be a number (e.g. `2012345`) or full key (e.g. `ubuntu/+source/foo/2012345`)
- **Search bugs**: `lpcli bug search <project> --search "<terms>"` — search bugs on a project
- **List bug tasks**: `lpcli bug tasks <bug-id>`
- **List comments**: `lpcli bug comments <bug-id>`
- **Add a comment**: `lpcli bug comment <bug-id> "<text>"`
- **Set status**: `lpcli bug set-status <bug-id> <status>` — e.g. `Fix Released`, `Triaged`, `Confirmed`, `Invalid`, `Won't Fix`, `New`
- **Set importance**: `lpcli bug set-importance <bug-id> <importance>` — e.g. `Critical`, `High`, `Medium`, `Low`, `Wishlist`
- **Set assignee**: `lpcli bug set-assignee <bug-id> <lp-username>`
- **Tag a bug**: `lpcli bug tag <bug-id> --add <tag>` or `--remove <tag>` or `--clear`
- **Subscriptions**: `lpcli bug subscriptions <bug-id>`, `lpcli bug subscribe <bug-id> <person>`, `lpcli bug unsubscribe <bug-id> <person>`
- **Add/delete tasks**: `lpcli bug add-task <bug-id> <target>`, `lpcli bug delete-task <bug-id> <target>`

## Person queries (`lpcli person`)

- **Show person**: `lpcli person show <username-or-team-name>`
- **Search people**: `lpcli person search "<name>"`
- **Team members**: `lpcli person members <team-name>`
- **Person's bugs**: `lpcli person bugs <username>` — bugs filed by or assigned to a person
- **PPAs**: `lpcli person ppas <username>`
- **Owned teams**: `lpcli person owned-teams <username>`

## Package queries (`lpcli package`)

- **Distro series info**: `lpcli package series <series>` — e.g. `noble`, `jammy`, `oracular`
- **List all series**: `lpcli package list-series`
- **Search source packages**: `lpcli package search --distro <series> "<package-name>"`
- **PPA info**: `lpcli package ppa <ppa-spec>` — e.g. `~user/ubuntu/my-ppa`
- **PPA source packages**: `lpcli package ppa-sources <ppa-spec>`
- **Distro info**: `lpcli package distro`

## Project queries (`lpcli project`)

- **Show project**: `lpcli project show <project-name>`
- **Search projects**: `lpcli project search "<terms>"`
- **List milestones**: `lpcli project milestones <project-name>`
- **Show milestone**: `lpcli project show-milestone <project-name> <milestone-name>`
- **List series**: `lpcli project list-series <project-name>`
- **Show series**: `lpcli project series-show <project-name> <series-name>`
- **Series releases**: `lpcli project series-releases <project-name> <series-name>`

## Git queries (`lpcli git`)

- **Show repo**: `lpcli git show <repo-path>` — e.g. `~owner/project/+git/name`
- **Default repo**: `lpcli git default <project-name>`
- **List person repos**: `lpcli git list-person-repos <username>`
- **List refs**: `lpcli git refs <repo-path>` — branches and tags
- **Merge proposals**: `lpcli git proposals <repo-path>`

## CVE queries (`lpcli cve`)

- **Show CVE**: `lpcli cve show <cve-id>` — e.g. `CVE-2024-1234`
- **Search CVEs**: `lpcli cve search "<terms>"`
- **CVEs linked to bug**: `lpcli cve bug-cves <bug-id>`

## Snap queries (`lpcli snap`)

- **Show recipe**: `lpcli snap show <snap-name>`
- **Find recipes**: `lpcli snap find <owner>`
- **Pending builds**: `lpcli snap builds <snap-name>`
- **Request builds**: `lpcli snap request-builds <snap-name>`

## Specification/blueprint queries (`lpcli spec`)

- **Show spec**: `lpcli spec show <project> <spec-name>`
- **List specs**: `lpcli spec list <project>`

## Question queries (`lpcli question`)

- **Show question**: `lpcli question show <question-id>`
- **Search questions**: `lpcli question search <project> --search "<terms>"`
- **Messages**: `lpcli question messages <question-id>`

## Webhook management (`lpcli webhook`)

- **List webhooks**: `lpcli webhook list <target>` — project, distro, or git repo
- **Create webhook**: `lpcli webhook create <target> <url>`
- **Delete webhook**: `lpcli webhook delete <target> <webhook-id>`
- **Ping webhook**: `lpcli webhook ping <target> <webhook-id>`
- **List deliveries**: `lpcli webhook deliveries <target> <webhook-id>`

## Tips

- Always run the command via bash and capture the output to present to the user in a readable format.
- If the user provides a Launchpad URL, extract the relevant identifier (bug number, project name, etc.) and use the appropriate `lpcli` subcommand.
- For searches, use `--search` flag with quoted terms. Some subcommands also support `--status`, `--importance`, and other filters — run `<subcommand> --help` if you need to discover additional options.
- If authentication is needed, check with `lpcli status` first. If not authenticated, guide the user to run `lpcli login`.
