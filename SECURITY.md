# Security Policy

## Supported Versions

This project is a small CLI published from `main`. Security fixes are applied to
the latest revision on the `main` branch.

| Version | Supported |
| ------- | --------- |
| latest `main` | Yes |

## Reporting a Vulnerability

Please **do not** report security vulnerabilities through public GitHub issues,
discussions, or pull requests.

Instead, use one of the following private channels:

1. Open a private report via GitHub's
   [security advisories](https://github.com/Ayinkx/drips-wave-helper/security/advisories/new).
2. Or email the maintainer at the address listed on the
   [GitHub profile](https://github.com/Ayinkx).

Please include:

- A description of the issue and its impact.
- Steps to reproduce (proof-of-concept if possible).
- The affected version/commit.
- Any suggested remediation.

You can expect an acknowledgement within a few days and a status update as the
report is triaged. Please give us a reasonable window to release a fix before any
public disclosure.

## Scope and Handling Secrets

This tool reads a GitHub token from the `GITHUB_TOKEN` (or `GH_TOKEN`)
environment variable and optional Discord/Telegram credentials from the
environment. It does **not** store them on disk.

- Never commit tokens, webhooks, or chat IDs. Use environment variables or
  repository secrets.
- Generated files (`state.json`, `data/`, `applications/`, `alert.md`,
  `dashboard.html`) may contain issue content; review them before sharing.

Thank you for helping keep the project and its users safe.
