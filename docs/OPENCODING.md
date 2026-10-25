# OpenCode setup for ERP03

## Local development
Use the wrapper to load secrets:
```bash
./scripts/opencode.sh
```
Secrets live in `~/.config/opencode/.env` and are never committed.

Project config: `.opencode/opencode.jsonc`
* MCP GitHub uses `{env:GITHUB_TOKEN}`
* Default agent `build`, permissions `auto`

## GitHub Actions automation
Workflow: `.github/workflows/opencode.yml`
* Triggers: issue/PR comment `/oc` or `/opencode`, manual dispatch
* Action: `anomalyco/opencode/github@latest`
* Requires repo secret `ANTHROPIC_API_KEY` and OpenCode GitHub App installed

## Secret rotation
* `GITHUB_TOKEN` – GitHub PAT with repo scope
* `ANTHROPIC_API_KEY` – Anthropic API key
* `TYPESAFE_API_KEY` – optional, set in `ERP-BACKEND/.env`

Never commit tokens. Use env interpolation `{env:VAR}` in OpenCode configs.
