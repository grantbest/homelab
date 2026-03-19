# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is
Self-hosted homelab infra (Cloudflare Tunnel, Traefik, Temporal, Vikunja, Postgres, Monitoring, Backup) plus the Gastown webhook listener and beads_manager for AI agent coordination.

## Key Directories
- `shared-services/` — core Docker Compose stack (all persistent services)
- `scripts/` — `webhook_listener.py`, `beads_manager.py`, and agent scripts
- `apps/betting-prod/` and `apps/betting-dev/` — BettingApp deployments

## Deploy Commands
```bash
# Rebuild and restart webhook-listener (after code changes)
cd shared-services && docker compose build webhook-listener && docker compose up -d webhook-listener

# Start all shared services + Monitoring
cd shared-services && docker compose up -d

# Check E2E Health
./tests/validate-homelab.sh
```

## Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization (`grafana.bestfam.us`)
- **Postgres Exporter**: DB metrics
- **cAdvisor**: Container metrics

## Backup Strategy
- **Postgres Backup**: Daily automated dumps of `mlb_engine`, `vikunja`, and `temporal` stored in `Homelab/shared-services/backups/`.
- 7-day retention period.

## Webhook Listener (`scripts/webhook_listener.py`)
Receives Vikunja webhooks and triggers Temporal MayorWorkflow.

**Anti-loop filters (do not remove):**
1. `[AGENT_SIGNATURE]` in description → ignore
2. `[BREAKDOWN_STARTED]` in description → ignore
3. Agent comments (`[AGENT_SIGNATURE]`) → ignore

## Beads Manager (REST Integration)
- Located at `BestFam-Orchestrator/scripts/beads_manager.py`.
- Shared utility for all agents to interact with the Vikunja REST API.

## Environment
`shared-services/.env` must contain:
- `VIKUNJA_API_TOKEN` — Vikunja bearer token
- `VIKUNJA_PROJECT_ID=2`
- `VIKUNJA_KANBAN_VIEW_ID=8`
- `TEMPORAL_ADDRESS=temporal:7233`
- `ANTHROPIC_API_KEY` (Optional, only for explicit Claude requests)
- `GEMINI_API_KEY` (Primary)
- `OPENAI_API_KEY` (Secondary)
