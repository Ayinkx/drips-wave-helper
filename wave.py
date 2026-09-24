#!/usr/bin/env python3
"""
drips-wave-helper
=================
Find, rank and draft applications for Stellar Wave (Drips) open issues.

This tool PREPARES applications for you (single account). It never posts for you —
you review each draft and submit it yourself on Drips/GitHub.

Quick start:
    python wave.py fetch        # pull all open stellar-wave issues
    python wave.py rank         # show them ranked against your skills
    python wave.py draft        # write a tailored draft for every open issue
    python wave.py dashboard    # build dashboard.html (copy + apply links)
    python wave.py status       # show how many of your slots you've used
    python wave.py mark Ayinkx/repo#12 --applied
    python wave.py open Ayinkx/repo#12
    python wave.py run          # fetch + draft + dashboard in one go
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib import error, parse, request

try:  # make Windows consoles happy with emoji output
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
APPS = ROOT / "applications"
CONFIG_PATH = ROOT / "config.json"
ISSUES_PATH = DATA / "issues.json"
STATE_PATH = ROOT / "state.json"
DASHBOARD_PATH = ROOT / "dashboard.html"
ALERT_PATH = ROOT / "alert.md"

API = "https://api.github.com"

DEFAULT_CONFIG = {
    "github_username": "Ayinkx",
    "display_name": "Ayinkx",
    "full_name": "Lawal Olayinka Awal",
    "roles": ["Python & Backend Developer", "Open Source Contributor"],
    "skills": [
        "Python", "Flask", "FastAPI", "REST API", "Docker", "SQL", "MySQL",
        "JavaScript", "TypeScript", "React", "Node", "HTML", "CSS",
        "Rust", "Soroban", "Stellar", "Web3", "Git", "Linux", "Bash",
        "Documentation", "Testing", "pytest"
    ],
    "labels": ["stellar-wave"],
    "slots": 15,
    "pitch": "I'm a self-taught Python & backend developer and open-source contributor. I focus on clean, tested code and love shipping real features end to end.",
    "links": {
        "github": "https://github.com/Ayinkx",
        "portfolio": "https://ayinkx-portfolio.vercel.app",
        "linkedin": "https://www.linkedin.com/in/ayinkx"
    },
    "addons": ["Please let me know if you'd like more detail on my plan."]
}

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def log(msg: str = "") -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config() -> dict:
    cfg = load_json(CONFIG_PATH, None)
    if cfg is None:
        save_json(CONFIG_PATH, DEFAULT_CONFIG)
        log(f"Created {CONFIG_PATH.name} — edit it with your details, then re-run.")
        cfg = dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def gh_token() -> str | None:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return None


def api_get(url: str, token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "drips-wave-helper",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        hint = ""
        if e.code == 403 and "rate limit" in body.lower():
            hint = "  (rate limited — set GITHUB_TOKEN or log in with `gh`)"
        raise SystemExit(f"GitHub API error {e.code}: {body[:200]}{hint}")
    except error.URLError as e:
        raise SystemExit(f"Network error: {e.reason}")


def word_in(hay: str, needle: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(needle.lower()) + r"(?![a-z0-9])", hay) is not None


def issue_key(it: dict) -> str:
    return f"{it['repo']}#{it['number']}"


def parse_ref(ref: str) -> str:
    ref = ref.strip()
    m = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", ref)
    if m:
        return f"{m.group(1)}#{m.group(2)}"
    m = re.search(r"([^/\s]+/[^/\s#]+)[#\s]+(\d+)", ref)
    if m:
        return f"{m.group(1)}#{m.group(2)}"
    return ref


# --------------------------------------------------------------------------- #
# core
# --------------------------------------------------------------------------- #


def fetch_issues(cfg: dict) -> list[dict]:
    token = gh_token()
    seen_keys = set(load_json(STATE_PATH, {}).get("seen", []))
    issues: dict[str, dict] = {}

    for label in cfg["labels"]:
        page = 1
        while True:
            q = parse.quote(f'label:"{label}" is:issue is:open')
            url = f"{API}/search/issues?q={q}&per_page=100&sort=updated&order=desc&page={page}"
            data = api_get(url, token)
            items = data.get("items", [])
            for it in items:
                repo = it["repository_url"].replace(f"{API}/repos/", "")
                key = f"{repo}#{it['number']}"
                issues[key] = {
                    "key": key,
                    "repo": repo,
                    "number": it["number"],
                    "title": it["title"],
                    "body": (it.get("body") or "")[:4000],
                    "url": it["html_url"],
                    "labels": [l["name"] for l in it.get("labels", [])],
                    "comments": it.get("comments", 0),
                    "created_at": it.get("created_at", ""),
                    "updated_at": it.get("updated_at", ""),
                }
            if len(items) < 100 or page >= 10:
                break
            page += 1

    result = list(issues.values())
    new_keys = [i["key"] for i in result if i["key"] not in seen_keys]
    save_json(ISSUES_PATH, result)

    if new_keys:
        state = load_json(STATE_PATH, {})
        state.setdefault("seen", [])
        for k in new_keys:
            if k not in state["seen"]:
                state["seen"].append(k)
        state["last_fetch"] = dt.datetime.now().isoformat(timespec="seconds")
        save_json(STATE_PATH, state)

    log(f"Fetched {len(result)} open stellar-wave issues.")
    if new_keys:
        log(f"🆕 {len(new_keys)} new since last run:")
        for k in new_keys[:20]:
            log(f"   - {k}")
    else:
        log("No new issues since last run.")
    return result, new_keys


def score_issue(it: dict, cfg: dict) -> tuple[int, list[str]]:
    text = f"{it['title']}\n{it.get('body') or ''}".lower()
    labels = [l.lower() for l in it.get("labels", [])]
    label_text = " ".join(labels)

    matched = [s for s in cfg["skills"] if word_in(text, s) or word_in(label_text, s)]
    s = len(matched) * 10

    bonuses = [
        ("good first issue", 25), ("good-first-issue", 25), ("help wanted", 10),
        ("frontend", 3), ("backend", 3), ("contract", 3), ("soroban", 4),
        ("documentation", 2), ("docs", 2), ("bug", 3), ("tests", 2), ("test", 2),
    ]
    for kw, bonus in bonuses:
        if kw in label_text or word_in(text, kw):
            s += bonus

    # fresher issues get a small nudge
    try:
        created = dt.datetime.fromisoformat(it["created_at"].replace("Z", "+00:00"))
        days = (dt.datetime.now(dt.timezone.utc) - created).days
        s += max(0, 14 - days)
    except Exception:
        pass

    return s, matched


def ranked(cfg: dict) -> list[dict]:
    issues = load_json(ISSUES_PATH, [])
    if not issues:
        raise SystemExit("No issues yet — run `python wave.py fetch` first.")
    out = []
    for it in issues:
        s, matched = score_issue(it, cfg)
        row = dict(it)
        row["score"] = s
        row["matched"] = matched
        out.append(row)
    out.sort(key=lambda r: r["score"], reverse=True)
    return out


def draft_text(it: dict, matched: list[str], cfg: dict) -> str:
    who = cfg["display_name"]
    full = cfg.get("full_name", who)
    roles = " · ".join(cfg["roles"])
    skills = ", ".join(matched[:6]) if matched else "Python and open-source tooling"
    links = " · ".join(v for v in cfg.get("links", {}).values())
    extra = "\n".join(f"- {a}" for a in cfg.get("addons", []))
    return f"""Hi! I'd love to pick this up.

**About me:** I'm {full} ({who}) — {roles}. I work with {skills}.

**Why this issue:** "{it['title']}" lines up well with what I do day to day, and I'd
rather ship a small, well-tested slice than a broad, risky change.

**My plan**
1. Read the issue, existing code and tests; ask anything unclear.
2. Implement the smallest correct change, with tests where it matters.
3. Open a PR early for feedback and iterate on review.

{cfg['pitch']}

**Links:** {links}

Happy to start right away — thanks for considering me!
{extra}
""".strip() + "\n"


def remaining_slots(cfg: dict) -> int:
    state = load_json(STATE_PATH, {})
    applied = state.get("applied", {})
    return max(0, int(cfg["slots"]) - len(applied))


def cmd_fetch(args, cfg):
    fetch_issues(cfg)


def cmd_rank(args, cfg):
    rows = ranked(cfg)
    top = rows[: args.top] if args.top else rows
    applied = load_json(STATE_PATH, {}).get("applied", {})
    log(f"{'SCORE':>6}  {'MATCHED':<28}  ISSUE")
    log("-" * 90)
    for r in top:
        mark = "✓" if r["key"] in applied else " "
        matched = ",".join(r["matched"][:4])
        log(f"{r['score']:>6}  {matched:<28.28}  [{mark}] {r['key']}  {r['title'][:60]}")


def cmd_draft(args, cfg):
    rows = ranked(cfg)
    applied = load_json(STATE_PATH, {}).get("applied", {})
    APPS.mkdir(exist_ok=True)
    n = 0
    for r in rows:
        if r["key"] in applied and not args.force:
            continue
        if args.top and n >= args.top:
            break
        safe = re.sub(r"[^a-zA-Z0-9]+", "-", r["key"]).strip("-")
        (APPS / f"{safe}.md").write_text(draft_text(r, r["matched"], cfg), encoding="utf-8")
        n += 1
    log(f"Wrote {n} draft(s) to {APPS.name}/  (review before posting!)")


def cmd_status(args, cfg):
    state = load_json(STATE_PATH, {})
    applied = state.get("applied", {})
    log(f"Slots used: {len(applied)} / {cfg['slots']}   (remaining: {remaining_slots(cfg)})")
    if applied:
        log("Applied:")
        for k, v in applied.items():
            log(f"  ✓ {k}  ({v.get('at', '')})")
    last = state.get("last_fetch", "never")
    log(f"Last fetch: {last}")


def cmd_mark(args, cfg):
    ref = parse_ref(args.ref)
    state = load_json(STATE_PATH, {})
    applied = state.setdefault("applied", {})
    if args.skip:
        applied.pop(ref, None)
        state.setdefault("skipped", {})
        state["skipped"][ref] = {"at": dt.datetime.now().isoformat(timespec="seconds")}
        log(f"Marked {ref} as SKIPPED")
    else:
        applied[ref] = {"at": dt.datetime.now().isoformat(timespec="seconds")}
        log(f"Marked {ref} as APPLIED  ({len(applied)}/{cfg['slots']} slots)")
    save_json(STATE_PATH, state)


def cmd_open_issue(args, cfg):
    rows = ranked(cfg)
    ref = parse_ref(args.ref)
    it = next((r for r in rows if r["key"] == ref), None)
    if not it:
        raise SystemExit(f"Issue {ref} not found in data — run `fetch` first.")
    draft = draft_text(it, it["matched"], cfg)
    copied = copy_clip(draft)
    log(f"Opening {it['url']}")
    log("Draft copied to clipboard." if copied else "Draft below (copy manually):")
    if not copied:
        log("-" * 60)
        log(draft)
    webbrowser.open(it["url"])
    log("Next: paste the draft and submit, then run "
        f"`python wave.py mark {it['key']} --applied`")


def copy_clip(text: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
        else:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
        return True
    except Exception:
        return False


def cmd_dashboard(args, cfg):
    rows = ranked(cfg)
    state = load_json(STATE_PATH, {})
    applied = state.get("applied", {})
    used = len(applied)

    cards = []
    for i, r in enumerate(rows, 1):
        is_applied = r["key"] in applied
        safe = re.sub(r"[^a-zA-Z0-9]+", "-", r["key"]).strip("-")
        draft = draft_text(r, r["matched"], cfg)
        draft_esc = html.escape(draft)
        tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in r["labels"][:6])
        matched = "".join(f'<span class="m">{html.escape(m)}</span>' for m in r["matched"][:6])
        cards.append(f"""
        <article class="card {'applied' if is_applied else ''}">
          <div class="row">
            <span class="rank">#{i}</span>
            <span class="score">{r['score']}</span>
            <span class="key">{html.escape(r['key'])}</span>
            {'<span class="badge">applied</span>' if is_applied else ''}
          </div>
          <h3>{html.escape(r['title'])}</h3>
          <div class="tags">{tags}</div>
          <div class="matched">match: {matched or '<i>—</i>'}</div>
          <details>
            <summary>Application draft</summary>
            <textarea readonly rows="10">{draft_esc}</textarea>
            <button class="copy" data-draft="{safe}">Copy draft</button>
          </details>
          <div class="actions">
            <a class="btn" href="{html.escape(r['url'])}" target="_blank" rel="noopener">Open issue ↗</a>
            <a class="btn ghost" href="https://www.drips.network/wave/stellar/issues" target="_blank" rel="noopener">Drips page ↗</a>
          </div>
        </article>""")

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Stellar Wave — application dashboard</title>
<style>
  :root{{--bg:#0d1117;--card:#161b22;--bd:#2a323c;--tx:#e6edf3;--mut:#9aa7b2;--ac:#00f7ff}}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:Inter,system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--tx);line-height:1.5}}
  header{{padding:28px 24px;border-bottom:1px solid var(--bd);position:sticky;top:0;background:rgba(13,17,23,.9);backdrop-filter:blur(8px);z-index:5}}
  h1{{margin:0;font-size:1.3rem}}
  .slots{{color:var(--ac);font-size:.9rem;margin-top:4px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px;padding:20px 24px 60px}}
  .card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px}}
  .card.applied{{border-color:#1f6f4a;opacity:.75}}
  .row{{display:flex;align-items:center;gap:8px;font-size:.82rem;color:var(--mut)}}
  .rank{{color:var(--ac);font-weight:700}}
  .score{{background:#20303f;border-radius:6px;padding:1px 7px}}
  .key{{font-family:ui-monospace,monospace}}
  .badge{{margin-left:auto;background:#1f6f4a;color:#fff;border-radius:999px;padding:1px 9px;font-size:.72rem}}
  h3{{font-size:1rem;margin:10px 0}}
  .tags .tag{{display:inline-block;font-size:.7rem;color:var(--mut);border:1px solid var(--bd);border-radius:6px;padding:1px 6px;margin:2px 4px 0 0}}
  .matched{{font-size:.78rem;color:var(--mut);margin:8px 0}}
  .matched .m{{color:var(--ac);margin-right:6px}}
  details summary{{cursor:pointer;color:var(--ac);font-size:.85rem;margin:6px 0}}
  textarea{{width:100%;background:#0b0f14;color:var(--tx);border:1px solid var(--bd);border-radius:8px;padding:10px;font-family:ui-monospace,monospace;font-size:.78rem}}
  .copy,.btn{{display:inline-block;margin-top:8px;background:var(--ac);color:#001a1f;border:0;border-radius:8px;padding:7px 12px;font-weight:600;font-size:.8rem;cursor:pointer;text-decoration:none}}
  .btn.ghost{{background:transparent;color:var(--ac);border:1px solid var(--bd)}}
  .actions{{display:flex;gap:8px;margin-top:10px}}
  .hint{{padding:0 24px;color:var(--mut);font-size:.82rem}}
</style></head>
<body>
<header>
  <h1>Stellar Wave — application dashboard</h1>
  <div class="slots">{used} / {cfg['slots']} slots used · {len(rows)} open issues</div>
</header>
<p class="hint">Drafts are prepared for you. Open the issue, paste your draft, submit — then mark it applied. This tool never posts for you.</p>
<div class="grid">{''.join(cards)}</div>
<script>
document.querySelectorAll('.copy').forEach(function(b){{
  b.addEventListener('click', function(){{
    var ta=b.closest('details').querySelector('textarea');
    navigator.clipboard.writeText(ta.value).then(function(){{
      b.textContent='Copied ✓'; setTimeout(function(){{b.textContent='Copy draft';}},1200);
    }});
  }});
}});
</script>
</body></html>"""
    DASHBOARD_PATH.write_text(doc, encoding="utf-8")
    log(f"Dashboard written to {DASHBOARD_PATH}")
    webbrowser.open(DASHBOARD_PATH.as_uri())


def cmd_ci(args, cfg):
    """Used by the GitHub Actions watcher: detect new issues and write alert.md."""
    issues, new_keys = fetch_issues(cfg)
    if not new_keys:
        log("No new issues — nothing to alert.")
        if ALERT_PATH.exists():
            ALERT_PATH.unlink()
        return

    rows = ranked(cfg)
    new_set = set(new_keys)
    new_rows = [r for r in rows if r["key"] in new_set]

    out = [
        f"# 🆕 {len(new_rows)} new Stellar Wave issue(s)",
        "",
        "Fresh issues matching your skills. **Open each one to apply** — this is just an alert.",
        "",
        "| # | Issue | Score | Matched |",
        "|---|-------|------:|---------|",
    ]
    for i, r in enumerate(new_rows, 1):
        out.append(f"| {i} | [{r['key']}]({r['url']}) — {r['title'][:70]} | {r['score']} | {', '.join(r['matched'][:4]) or '—'} |")
    out += ["", "## Drafts", ""]
    for r in new_rows:
        out += [
            f"### [{r['key']}]({r['url']}) — {r['title']}",
            "",
            "<details><summary>Application draft</summary>",
            "",
            "```",
            draft_text(r, r["matched"], cfg).strip(),
            "```",
            "",
            "</details>",
            "",
        ]
    ALERT_PATH.write_text("\n".join(out), encoding="utf-8")
    log(f"Wrote {ALERT_PATH.name} with {len(new_rows)} new issue(s).")


def cmd_run(args, cfg):
    fetch_issues(cfg)
    rows = ranked(cfg)
    applied = load_json(STATE_PATH, {}).get("applied", {})
    APPS.mkdir(exist_ok=True)
    budget = remaining_slots(cfg)
    picked = [r for r in rows if r["key"] not in applied][:budget] if budget else []
    for r in picked:
        safe = re.sub(r"[^a-zA-Z0-9]+", "-", r["key"]).strip("-")
        (APPS / f"{safe}.md").write_text(draft_text(r, r["matched"], cfg), encoding="utf-8")
    log(f"Prepared {len(picked)} draft(s) for your {budget} remaining slot(s).")
    cmd_dashboard(argparse.Namespace(), cfg)


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #


def main():
    p = argparse.ArgumentParser(description="Prepare Stellar Wave (Drips) applications — for your own single account.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fetch", help="fetch all open stellar-wave issues").set_defaults(func=cmd_fetch)

    pr = sub.add_parser("rank", help="rank issues against your skills")
    pr.add_argument("--top", type=int, default=0)
    pr.set_defaults(func=cmd_rank)

    pd = sub.add_parser("draft", help="write application drafts")
    pd.add_argument("--top", type=int, default=0)
    pd.add_argument("--force", action="store_true", help="also redraft already-applied issues")
    pd.set_defaults(func=cmd_draft)

    sub.add_parser("status", help="show slot usage").set_defaults(func=cmd_status)

    pm = sub.add_parser("mark", help="mark an issue applied/skipped")
    pm.add_argument("ref", help="owner/repo#123 or the issue URL")
    pm.add_argument("--applied", action="store_true")
    pm.add_argument("--skip", action="store_true")
    pm.set_defaults(func=cmd_mark)

    po = sub.add_parser("open", help="open an issue + copy its draft")
    po.add_argument("ref")
    po.set_defaults(func=cmd_open_issue)

    sub.add_parser("dashboard", help="build dashboard.html").set_defaults(func=cmd_dashboard)
    sub.add_parser("ci", help="CI mode: detect new issues and write alert.md").set_defaults(func=cmd_ci)
    sub.add_parser("run", help="fetch + draft remaining slots + dashboard").set_defaults(func=cmd_run)

    args = p.parse_args()
    cfg = load_config()
    args.func(args, cfg)


if __name__ == "__main__":
    main()
