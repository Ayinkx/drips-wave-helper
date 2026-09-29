# drips-wave-helper

[![CI](https://github.com/Ayinkx/drips-wave-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/Ayinkx/drips-wave-helper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](pyproject.toml)

A small, dependency-free CLI that helps a contributor find, rank and draft
applications for **Stellar Wave (Drips)** open issues.

It is a **single-account helper**: it does the heavy lifting of discovery,
scoring and writing a tailored draft, but it never posts anything for you.
You review every draft and submit it yourself.

## Features

- **Fetch** every open `stellar-wave` issue from the GitHub API.
- **Rank** issues against your configured skills and interests.
- **Draft** a tailored application message per issue in Markdown.
- **Track slots** so you always know how many applications you have left.
- **Detect freed slots** by checking whether your applied issues were closed or
  assigned to someone else.
- **Dashboard** — build a local `dashboard.html` with copy + apply links.
- **Notifications** — optional Discord and Telegram alerts for new issues.
- **CI mode** — a scheduled GitHub Action that watches for new issues and can
  commit state automatically.

## Requirements

- Python **3.9+**
- No third-party runtime dependencies (standard library only).
- A GitHub token in `GITHUB_TOKEN` (or `GH_TOKEN`) is recommended to avoid
  rate limits: `export GITHUB_TOKEN=ghp_...`

## Quick start

```bash
git clone https://github.com/Ayinkx/drips-wave-helper.git
cd drips-wave-helper

python wave.py fetch        # pull all open stellar-wave issues
python wave.py rank --top 20  # rank them against your skills
python wave.py draft        # write a tailored draft for every open issue
python wave.py dashboard    # build dashboard.html (copy + apply links)
python wave.py status       # show how many of your slots you have used
```

Then work each issue:

```bash
python wave.py mark Ayinkx/repo#12 --applied
python wave.py open Ayinkx/repo#12
python wave.py slots         # which applied issues have freed up?
python wave.py refill        # draft applications to refill free slots

python wave.py run           # fetch + draft + dashboard in one go
```

## Commands

| Command      | Description                                                        |
| ------------ | ------------------------------------------------------------------ |
| `fetch`      | Fetch all open `stellar-wave` issues.                              |
| `rank`       | Rank issues against your skills (`--top N` to limit output).       |
| `draft`      | Write application drafts (`--top N`, `--force` to redraft).        |
| `status`     | Show slot usage.                                                    |
| `slots`      | Check which of your applied issues have freed up.                  |
| `refill`     | Prepare drafts to refill free slots.                               |
| `noapps`     | List the freshest open issues with no applications yet.            |
| `mark`       | Mark an issue applied/skipped: `mark owner/repo#123 --applied`.    |
| `open`       | Open an issue in the browser and copy its draft to the clipboard.  |
| `dashboard`  | Build `dashboard.html`.                                             |
| `ci`         | CI mode: detect new issues and write `alert.md`.                   |
| `test-notify`| Send a test Discord + Telegram alert.                              |
| `run`        | Fetch + draft remaining slots + dashboard.                         |

## How ranking works

Each issue is scored from its title, body and labels:

- **Skill matches** — every configured skill found as a whole word adds `10`.
- **Bonuses** — `good first issue` (+25), `help wanted` (+10), and small nudges
  for `frontend`, `backend`, `contract`, `soroban`, `docs`, `bug` and `test`
  keywords.
- **Freshness** — issues created in the last 14 days receive a small nudge.

Skill matching is word-aware (a search for `python` will **not** match
`micropython`) and case-insensitive.

## Configuration

Everything is driven by [`config.json`](config.json), which is created with
sensible defaults on first run. Key fields:

| Field             | Purpose                                             |
| ----------------- | --------------------------------------------------- |
| `github_username` | Your GitHub handle (used to filter assignments).    |
| `display_name`    | Name used in drafted applications.                  |
| `full_name`       | Full name used in drafted applications.             |
| `roles`           | Short role list included in drafts.                 |
| `skills`          | Skills used for ranking and drafts.                 |
| `labels`          | GitHub labels to fetch (default `stellar-wave`).    |
| `wave_program_id` | Drips Wave program id used for the no-apps query.   |
| `slots`           | How many active applications you allow yourself.    |
| `pitch`           | A sentence about you, reused in every draft.        |
| `links`           | Links included at the bottom of drafts.             |
| `addons`          | Extra Markdown bullet lines appended to drafts.     |

## Notifications (optional)

Set these environment variables / repository secrets to enable alerts:

| Variable              | Provider          |
| --------------------- | ----------------- |
| `DISCORD_WEBHOOK`     | Discord webhook   |
| `TELEGRAM_BOT_TOKEN`  | Telegram bot      |
| `TELEGRAM_CHAT_ID`    | Telegram chat id  |

Run `python wave.py test-notify` to verify them.

## Automation

[`.github/workflows/watch.yml`](.github/workflows/watch.yml) runs every 15
minutes, detects new issues and commits the updated `state.json`. It can also be
triggered manually (`workflow_dispatch`).

## Project structure

```
wave.py                      # the CLI (standard library only)
config.json                  # your profile, skills and preferences
state.json                   # seen issues + application state
dashboard.html               # generated locally (git-ignored)
data/                        # cached API responses (git-ignored)
applications/                # generated drafts (git-ignored)
tests/                       # pytest suite
```

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Security

Please report vulnerabilities privately — see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Lawal Olayinka Awal (Ayinkx)

## Disclaimer

This is an unofficial community tool and is not affiliated with or endorsed by
Drips or the Stellar Development Foundation. Use it responsibly and always
respect each project's contribution guidelines.
