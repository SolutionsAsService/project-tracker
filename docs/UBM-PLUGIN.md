# Plugin contract (for UBM and other hosts)

The tracker publishes two stable things. A host needs nothing else: no API key, no build step.

| What | URL |
|---|---|
| Data | `https://solutionsasservice.github.io/project-tracker/data/status.json` |
| Web component | `https://solutionsasservice.github.io/project-tracker/widget.js` |
| Iframe page | `https://solutionsasservice.github.io/project-tracker/?group=Autheo&compact` |

Data refreshes every 6 hours (cron `17 */6 * * *`) and on each push. GitHub Pages serves it with CORS
`Access-Control-Allow-Origin: *`, so a browser app on any origin can `fetch()` it.

## Option A: web component

```html
<script src="https://solutionsasservice.github.io/project-tracker/widget.js" defer></script>
<project-tracker src="https://solutionsasservice.github.io/project-tracker/data/status.json" group="Autheo" compact></project-tracker>
```

Attributes: `src` (required off-site), `group` (show one group), `compact` (hide one-liners and details).
Styles live in shadow DOM; it follows `prefers-color-scheme`. Override colours from the host with CSS custom
properties on the element: `--bg --card --ink --muted --line --green --amber --red --accent`.

## Option B: iframe

`<iframe src="https://solutionsasservice.github.io/project-tracker/?group=Autheo&compact" style="width:100%;height:600px;border:0"></iframe>`

## Option C: read the JSON (recommended for a native plugin)

### status.json, `schema_version: 1`

```jsonc
{
  "schema_version": 1,                 // integer; bumped only on breaking changes
  "generated_at": "2026-10-13T22:40:00+00:00",
  "title": "SolutionsAsService projects",
  "north_star": "string | null",
  "groups": ["Autheo", "Drones & hardware", "Agents & tools", "Business systems"],   // display order
  "projects": [
    {
      "id": "agent-env",               // stable key, unique
      "name": "Autheo Agent Environment",
      "group": "Autheo",               // one of groups[]
      "visibility": "public",          // "public" | "private"
      "details": "full",               // "full" | "public-safe"  (public-safe = only the fields marked * below)
      "one_line": "string",            // *
      "state": "doing",                // *  backlog | doing | blocked | done
      "rag": "green",                  // *  green | amber | red
      "depends_on": ["other-id"],      // *
      "progress": 40,                  // *  0-100 or null
      "progress_source": "manual",     // *  "manual" | "github-milestone:<title>" | null
      "stale": false,                  // *  true | false | null (null = no commit data)
      "days_since_commit": 0,          // *  integer | null
      "live": { ... } | null,          // *  null for public-safe projects
      "live_error": "string",          //    present only when a full project's repo could not be read

      // details == "full" only (ledger fields, PMDAA names):
      "repo": "owner/name",
      "north_star": "string",
      "rag_evidence": "string",
      "milestone": {"id": "M1", "name": "string", "exit_test": "string"},
      "next_actions": [{"action": "string", "owner": "string", "status": "todo|doing|done"}],
      "raid": [...], "decisions": [...], "evidence": {...}   // passed through when present
    }
  ]
}
```

`live` (only when GitHub was read):

```jsonc
{
  "visibility": "public", "url": "https://github.com/owner/name", "description": "string | null",
  "stars": 1, "open_issues": 0, "open_prs": 0, "languages": ["Python", "HTML"],   // top 4 by bytes
  "head": "2adb938", "head_date": "ISO-8601", "head_subject": "first line of the commit message",
  "ci": "success",                     // success | failure | pending | none  (all runs on the HEAD commit)
  "ci_url": "string | null",
  "milestones": [{"title": "v1", "open": 2, "closed": 3, "due_on": "ISO-8601 | null"}]   // open milestones, soonest due first
}
```

### Rules for consumers

- Check `schema_version === 1`; refuse or degrade on anything else.
- New fields may be added in v1 without a bump; ignore unknown fields.
- Treat `details: "public-safe"` projects as summary only; never try to look up their repo.
- `rag` is the owner's judgement; `live.ci` and `stale` are machine facts. Show both; do not merge them.
- Cache for up to 6 hours; `generated_at` says how old the data is.
