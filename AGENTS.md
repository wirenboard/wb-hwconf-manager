# Repository Guidelines

## Project Structure & Module Organization
- `config.py`: Core Python CLI for converting and validating hardware config JSON.
- `wb-hwconf-helper`, `functions.sh`, `init.sh`: Shell tooling to apply overlays and manage slots.
- `modules/`: Device Tree overlays (`.dtso/.dtsi`), per‑module scripts, and JSON schemas.
- `boards/`: Board presets (`*.conf`) used to resolve compatible slots.
- `slots/`: Slot definitions and helpers used during preprocessing.
- `test/config/`: Pytest fixtures and tests for `config.py` logic.
- `debian/`: Packaging metadata; CI expects Python checks and coverage.

## Build, Test, and Development Commands
- `make test`: Run unit tests via pytest with verbose output.
- `python3 -m pytest -vv`: Direct test run (used by CI); writes coverage in CI.
- `make install DESTDIR=./dist`: Stage installable files (uses `jq`, `dtc`, `tcc`).
- `./wb-hwconf-helper confed-tojson < /etc/wb-hardware.conf`: Produce JSON for UI.
- `./wb-hwconf-helper confed-fromjson < confed.json`: Apply edited JSON to config and run hooks.

## Coding Style & Naming Conventions
- Python: Black (line length 110) + isort (profile=black). Run: `black . && isort .`.
- Lint: Pylint (py39 rules; snake_case for functions/vars, PascalCase for classes). Run: `pylint config.py`.
- Shell: POSIX/Bash, keep functions small; use existing helpers in `functions.sh`.
- File naming: modules as `modules/<id>.dtso`, board presets `boards/<board>.conf`.

## Testing Guidelines
- Framework: pytest under `test/config/`.
- Coverage: CI minimum 81% (see `Jenkinsfile`). Add tests for new parsing/merging paths.
- Conventions: keep fixtures small; prefer deterministic JSON comparisons (see `test_config.py`).
- Run locally: `python3 -m pytest -vv test/config/test_config.py`.

## Commit & Pull Request Guidelines
- Messages: Imperative, concise subject; reference PRs/issues (e.g., "Add HDMI mode (#144)").
- Scope: Touch only related files; include sample config or schema updates when changing modules.
- PRs: Include description, rationale, testing notes, and before/after examples. Attach logs if touching shell scripts.

## Security & Configuration Tips
- Hardware‑affecting commands require root and mounted `configfs`. Avoid running on production boards during development.
- Validate JSON with `jq` and schemas in `modules/*.schema.json`. Keep vendor overrides in `/usr/share/wb-hwconf-manager/vendor-modules.json`.

