# Homelab: CD Control Plane
## Strategy: GitOps Pull & Sync

1. **Trigger:** Repository update or Webhook from BettingApp.
2. **Pull:** GitHub Runner pulls latest images from GHCR.
3. **Sync:** `docker compose up -d --remove-orphans` across:
   - `apps/betting-prod/` (Production Environment)
   - `apps/betting-dev/` (Development Environment)
4. **Validate:** Execute `Homelab/tests/validate-homelab.sh`.
