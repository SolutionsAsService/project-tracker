#!/usr/bin/env python3
"""Build site/data/status.json from one or more ledgers (projects.yaml, or a PMDAA PORTFOLIO.yaml) + the GitHub API.

Privacy: a private project is reduced to PUBLIC_SAFE fields unless it sets show_private_details: true
AND TRACKER_TOKEN is set. Public repos are read with GITHUB_TOKEN (sees public repos only).
"""
import datetime as dt, json, os, sys, urllib.error, urllib.request
import yaml

SCHEMA_VERSION = 1
# Same list as PMDAA's public-safe rule (ledger-format.md), plus our group/progress.
PUBLIC_SAFE = ("id", "name", "group", "visibility", "one_line", "state", "rag", "depends_on", "progress")
API = "https://api.github.com"


def get(path, token):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "project-tracker"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (404, 403, 409):  # missing/no access/empty repo
            return None
        raise


def ci_summary(runs):
    # PMDAA rule: CI on HEAD = all success -> success, any running -> pending, other -> failure, none -> none
    if not runs:
        return "none"
    if any(r["status"] != "completed" for r in runs):
        return "pending"
    return "success" if all(r["conclusion"] in ("success", "skipped", "neutral") for r in runs) else "failure"


def fetch_live(repo, token):
    meta = get(f"/repos/{repo}", token)
    if not meta:
        return None
    commits = get(f"/repos/{repo}/commits?per_page=1", token) or []
    head = commits[0] if commits else None
    runs = (get(f"/repos/{repo}/actions/runs?head_sha={head['sha']}&per_page=50", token) or {}).get("workflow_runs", []) if head else []
    pulls = get(f"/repos/{repo}/pulls?state=open&per_page=100", token) or []
    milestones = get(f"/repos/{repo}/milestones?state=open&sort=due_on&per_page=10", token) or []
    langs = get(f"/repos/{repo}/languages", token) or {}
    return {
        "visibility": meta["visibility"],
        "url": meta["html_url"],
        "description": meta.get("description"),
        "stars": meta["stargazers_count"],
        "open_prs": len(pulls),
        "open_issues": meta["open_issues_count"] - len(pulls),  # GitHub counts PRs as issues
        "languages": sorted(langs, key=langs.get, reverse=True)[:4],
        "head": head["sha"][:7] if head else None,
        "head_date": head["commit"]["committer"]["date"] if head else None,
        "head_subject": head["commit"]["message"].splitlines()[0][:140] if head else None,
        "ci": ci_summary(runs),
        "ci_url": runs[0]["html_url"] if runs else None,
        "milestones": [{"title": m["title"], "open": m["open_issues"], "closed": m["closed_issues"], "due_on": m["due_on"]} for m in milestones],
    }


def project_status(p, group, stale_days, now, tokens):
    p = dict(p, group=p.get("group") or group)
    if (p.get("repos") or {}).get("public"):  # PMDAA pair: live facts from the public repo; the private one is a name only
        p["repo"] = p["repos"]["public"]
    private = p.get("visibility", "public") != "public"
    detailed = not private or (p.get("show_private_details") is True and bool(tokens["private"]))
    live = None
    if p.get("repo") and detailed:
        live = fetch_live(p["repo"], tokens["private"] if private else tokens["public"])
        if live and live["visibility"] != "public" and not private:
            # ledger says public but GitHub says private: never leak, fall back to the safe view
            private, detailed, live = True, False, None
            p["visibility"] = "private"
    out = {k: p[k] for k in (PUBLIC_SAFE if not detailed else p) if k in p and k not in ("show_private_details", "local")}
    if not detailed:
        out.pop("repo", None)
    out["details"] = "full" if detailed else "public-safe"
    out["live"] = live
    if detailed and p.get("repo") and live is None:
        out["live_error"] = "repo not found or not readable with the current token"
    days = None
    if live and live["head_date"]:
        days = (now - dt.datetime.fromisoformat(live["head_date"].replace("Z", "+00:00"))).days
    out["days_since_commit"] = days
    out["stale"] = None if days is None else days > stale_days
    if p.get("progress") is not None:
        out["progress"], out["progress_source"] = int(p["progress"]), "manual"
    elif live and live["milestones"] and (live["milestones"][0]["open"] + live["milestones"][0]["closed"]):
        m = live["milestones"][0]
        out["progress"], out["progress_source"] = round(100 * m["closed"] / (m["open"] + m["closed"])), "github-milestone:" + m["title"]
    else:
        out["progress"], out["progress_source"] = None, None
    return out


def build(ledgers, tokens, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    projects, groups = [], []
    for led in ledgers:
        stale_days = int(led.get("stale_days", 14))
        for p in led.get("projects") or []:
            s = project_status(p, led.get("portfolio", "Projects"), stale_days, now, tokens)
            projects.append(s)
            if s["group"] not in groups:
                groups.append(s["group"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now.isoformat(timespec="seconds"),
        "title": ledgers[0].get("title", "Projects"),
        "north_star": ledgers[0].get("north_star"),
        "groups": groups,
        "projects": projects,
    }


def main(argv):
    paths = argv[1:] or ["projects.yaml"]
    ledgers = [yaml.safe_load(open(x, encoding="utf-8")) for x in paths]
    tokens = {"public": os.environ.get("GITHUB_TOKEN"), "private": os.environ.get("TRACKER_TOKEN")}
    data = build(ledgers, tokens)
    os.makedirs("site/data", exist_ok=True)
    with open("site/data/status.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"wrote site/data/status.json: {len(data['projects'])} projects")


if __name__ == "__main__":
    main(sys.argv)
