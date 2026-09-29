# Contributing to drips-wave-helper

Thanks for your interest in improving `drips-wave-helper`! This document explains
how to set up the project, the standards we follow, and how to get your change
merged.

## Code of Conduct

By participating you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behaviour to
the maintainer.

## Getting started

```bash
# 1. Fork the repository and clone your fork
git clone https://github.com/<your-user>/drips-wave-helper.git
cd drips-wave-helper

# 2. Install development dependencies (runtime has none)
python -m pip install -r requirements-dev.txt

# 3. Run the test suite
python -m pytest -q
```

The project targets **Python 3.9+** and uses only the standard library at
runtime, so there is nothing else to install to run `wave.py`.

## Ways to contribute

- **Report a bug** using the bug report issue template.
- **Request a feature** using the feature request template.
- **Improve documentation** — the README and docstrings are fair game.
- **Write tests** — new behaviour should come with tests.
- **Pick up a `good first issue`** — these are scoped to be approachable.

Look for issues labelled [`good first issue`](https://github.com/Ayinkx/drips-wave-helper/labels/good%20first%20issue)
or [`help wanted`](https://github.com/Ayinkx/drips-wave-helper/labels/help%20wanted).

## Development workflow

1. Create a topic branch off `main`:
   `git checkout -b feat/short-description`.
2. Make your change in small, focused commits.
3. Add or update tests under `tests/`.
4. Run the checks locally:

   ```bash
   python -m pytest -q
   python -m py_compile wave.py
   ```

5. Open a pull request and fill in the template.

## Coding standards

- Keep the runtime **dependency-free** unless there is a strong reason; prefer
  the standard library.
- Follow the existing style: 4-space indentation, type hints where helpful,
  clear function names and a short docstring for non-obvious logic.
- Keep functions small and testable; isolate network calls so pure logic can be
  unit tested without hitting the API.
- Never commit secrets, tokens or personal data. `state.json` and generated
  files under `data/` and `applications/` should stay out of commits.

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add JSON output to the rank command
fix: handle repositories renamed after a draft was created
docs: clarify the notifications setup
test: cover parse_ref edge cases
chore: bump dev dependencies
```

## Pull requests

- Reference the issue your PR closes (`Closes #123`).
- Describe **what** changed and **why**, and how you tested it.
- Keep the PR focused; unrelated refactors belong in separate PRs.
- Ensure the CI workflow is green.

A maintainer will review as soon as possible. Please be responsive to review
comments; PRs that go stale may be closed.

## Reporting security issues

Do **not** open a public issue for security problems — see
[SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
