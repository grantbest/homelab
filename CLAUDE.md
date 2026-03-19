# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is
Self-hosted homelab infra (Cloudflare Tunnel, Traefik, Temporal, Vikunja, Postgres, Nexus, Promtail) plus the Gastown webhook listener and beads_manager for AI agent coordination.

## Key Directories
- `shared-services/` — core Docker Compose stack (all persistent services)
- `scripts/` — `webhook_listener.py`, `beads_manager.py`, and agent scripts
- `apps/betting-prod/` and `apps/betting-dev/` — BettingApp deployments

## Deploy Commands
```bash
# Rebuild and restart webhook-listener (after code changes)
cd shared-services && docker compose build webhook-listener && docker compose up -d webhook-listener

# Restart all shared services
cd shared-services && docker compose up -d

# BettingApp prod
cd apps/betting-prod && docker-compose up -d --build

# Check webhook logs
docker logs webhook-listener --tail=50
docker logs webhook-listener 2>&1 | grep -E "(SUCCESS|ignored|Task 170)"
```

## Webhook Listener (`scripts/webhook_listener.py`)
Receives Vikunja webhooks and triggers Temporal MayorWorkflow.

**Anti-loop filters (do not remove):**
1. `[AGENT_SIGNATURE]` in description + bucket=Design → ignore (prevents design doc re-triggers)
2. `[BREAKDOWN_STARTED]` in description + bucket=Doing → ignore (prevents epic breakdown loops)
3. Agent comments (`[AGENT_SIGNATURE]` in comment body) → ignore
4. `task.updated` bucket moves use deterministic IDs only — if workflow already ran, return `skipped` (no timestamp fallback)

**Bucket map**: Design, Doing, Validation trigger MayorWorkflow. To-Do and Done are ignored.

**Design comment replies** (`task.comment.created` in Design) → start `DesignRefine` path with timestamp ID (genuinely iterative, can run multiple times).

## Beads Manager (`scripts/beads_manager.py`)
Vikunja task CRUD. Key notes:
- `move_to_bucket()` uses `GET /api/v1/projects/{id}/views/{view_id}/buckets` — NOT `/projects/{id}/buckets` (returns 404)
- `VIKUNJA_KANBAN_VIEW_ID=8` (set in `shared-services/.env`)
- `bucket_id` is NOT returned by `GET /tasks/{id}` — only appears in webhook payloads
- Legacy fallback: if `VIKUNJA_API_TOKEN` not set, uses local `.beads/` JSON files

## Postgres
`max_connections=500`, `shared_buffers=256MB` — set in `shared-services/docker-compose.yml` command.
Vikunja pool: `VIKUNJA_DATABASE_MAXOPENCONNECTIONS=20`, `VIKUNJA_DATABASE_MAXIDLECONNECTIONS=10`.

## Environment
`shared-services/.env` must contain:
- `VIKUNJA_API_TOKEN` — Vikunja bearer token
- `VIKUNJA_PROJECT_ID=2`
- `VIKUNJA_KANBAN_VIEW_ID=8`
- `TEMPORAL_ADDRESS=temporal:7233`
