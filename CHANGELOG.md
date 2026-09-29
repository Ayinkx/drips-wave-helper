# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Contributor documentation: `README.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md` and issue/PR templates.
- Test suite (`tests/`) covering word-aware skill matching, reference parsing,
  issue scoring, draft generation and state helpers.
- CI workflow running the test suite and a syntax check on every push and PR.
- `pyproject.toml` with project metadata and tool configuration.

## [0.1.0] - 2026-09-29

### Added

- Dependency-free CLI (`wave.py`) to fetch, rank and draft applications for
  Stellar Wave (Drips) issues.
- Commands: `fetch`, `rank`, `draft`, `status`, `slots`, `refill`, `noapps`,
  `mark`, `open`, `dashboard`, `ci`, `test-notify`, `run`.
- Optional Discord and Telegram notifications for new issues.
- Scheduled GitHub Action (`watch.yml`) that tracks new issues and commits
  updated state.

[Unreleased]: https://github.com/Ayinkx/drips-wave-helper/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ayinkx/drips-wave-helper/releases/tag/v0.1.0
