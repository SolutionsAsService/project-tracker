# Project tracker

Live status of SolutionsAsService projects: **https://solutionsasservice.github.io/project-tracker/**

A GitHub Actions workflow rebuilds the page every 6 hours, on every push to `main`, and on manual dispatch
(Actions → *Build and deploy tracker* → Run workflow). It reads `projects.yaml`, asks the GitHub API for live
facts, writes `site/data/status.json` and deploys `site/` to GitHub Pages.

## What each card shows

From `projects.yaml` (you write it): name, group, one-line status, state, RAG (green = on track, amber = at risk,
red = off track), current milestone + exit test, next actions, optional manual progress.

From GitHub (public repos): last commit date + message, CI result on the latest commit, open issues and PRs,
open milestone progress, top languages, stars. A project is **stale** when its last commit is older than
`stale_days` (default 14).

Progress = `progress:` from the YAML if set, otherwise closed/total issues of the repo's first open GitHub
milestone (soonest due), otherwise no bar.

## Add a project

Add an entry to `projects.yaml` and push:

```yaml
- id: my-thing                    # unique
  name: My thing
  group: Agents & tools           # cards are grouped by this
  repo: SolutionsAsService/my-thing
  visibility: public              # public | private  (must match GitHub)
  one_line: What it is and where it stands, in one line.
  north_star: What it is for.
  state: doing                    # backlog | doing | blocked | done
  rag: green                      # green | amber | red
  rag_evidence: Why that colour (CI run, exit test, link).
  milestone: {id: M1, name: First release, exit_test: A test a stranger could run, with a threshold.}
  next_actions:
  - {action: The concrete next thing, owner: SolutionsAsService, status: todo}
  progress: 40                    # optional, 0-100; omit to use the GitHub milestone
```

A project with one public and one private repo (PMDAA pair) uses `repos: {public: owner/name, private: owner/name}`
instead of `repo:`. Live facts come from the public repo; the private repo is shown by name only.

## Privacy

- The workflow's `GITHUB_TOKEN` can only read **public** repos.
- A project with `visibility: private` is published as **name, group, one_line, state, RAG, progress and
  depends_on only**. Its repo name, milestone, next actions, commit messages and every other field are dropped
  from `status.json`, and GitHub is not queried for it.
- Live private data appears only if **both** are true: a repo secret `TRACKER_TOKEN` exists (a fine-grained token
  with read-only *Contents*, *Metadata*, *Issues*, *Pull requests*, *Actions* on the chosen repos) **and** the
  project sets `show_private_details: true`. Default is off. Anything then shown is public on the internet.
- If a project says `public` but GitHub reports it private, the build falls back to the summary-only view.
- `projects.yaml` itself is public: write only public-safe text in private projects' `one_line`.

The safe field list is the same as the PMDAA public-safe rule.

## PMDAA alignment

`projects.yaml` uses the PMDAA ledger format (ThothDivision/PMDAA, `skills/pmdaa/references/ledger-format.md`):
same field names (`id, name, repo, visibility, one_line, north_star, state, rag, rag_evidence, milestone{id,name,exit_test},
next_actions[{action,owner,status}], depends_on, raid, decisions`) plus three extras: `group`, `progress`,
`show_private_details`. A PMDAA `PORTFOLIO.yaml` can be fed in directly:
`python build.py projects.yaml path/to/PORTFOLIO.yaml` (its `portfolio:` name becomes the group when a project has none).
The tracker never writes back to a ledger; PMDAA's `live` block is ignored here and re-fetched.

## Embed / plugin

`data/status.json` is a versioned contract and `widget.js` is a drop-in web component. See
[docs/UBM-PLUGIN.md](docs/UBM-PLUGIN.md).

## Local run

```bash
pip install pyyaml
python -m unittest -v test_build
GITHUB_TOKEN=... python build.py   # writes site/data/status.json
python -m http.server -d site 8000
```
