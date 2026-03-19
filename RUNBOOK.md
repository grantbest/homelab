# BestFam SRE Runbook v1.0

This document serves as the primary knowledge base for the **SRE Agent**.

## 1. Temporal Orchestration Failures
- **Symptom:** "Connection Refused" or "Timeout" in worker logs.
- **Cause:** `temporal` container is down or starting slowly.
- **Resolution:**
    1. Check `docker ps` for `temporal`.
    2. Check `docker logs temporal`.
    3. Ensure `POSTGRES_USER` and `POSTGRES_PWD` match the `postgres` container.
    4. Restart the stack: `docker-compose up -d temporal`.

## 2. SOPS Decryption Failures
- **Symptom:** `pipeline.sh` fails at `[1/4] Decrypting Secrets`.
- **Cause:** Missing or incorrect `SOPS_AGE_KEY_FILE`.
- **Resolution:**
    1. Verify file exists: `ls -la /Users/grantbest/.sops_age_key.txt`.
    2. Check public key: `grep "public key" /Users/grantbest/.sops_age_key.txt`.
    3. Ensure `.sops.yaml` contains the correct public key.
    4. If key is lost, reconstruct `.env` from `.env.example` and re-encrypt.

## 3. Docker Build Context Issues
- **Symptom:** Pipeline hangs for minutes at "Updating: shared-services".
- **Cause:** Large `node_modules` or `.venv` being sent to Docker daemon.
- **Resolution:**
    1. Verify `.dockerignore` exists in the project root.
    2. Ensure `node_modules`, `.git`, and `.venv` are excluded.

## 4. Port Conflicts (3000/3001)
- **Symptom:** `betting-prod-dashboard` or `betting-dev-dashboard` fail to start.
- **Cause:** Local `npm run dev` or another container is using the port.
- **Resolution:**
    1. Check ports: `lsof -i :3000` or `lsof -i :3001`.
    2. Kill offending process: `kill -9 <PID>`.
    3. Restart container.

## 5. Bead (Task) Invisibility
- **Symptom:** Worker logs show `FileNotFoundError: Bead ... not found`.
- **Cause:** Mismatched volume mounts or `beads_manager.py` paths.
- **Resolution:**
    1. Ensure `Homelab/.beads` and `BettingApp/.beads` are mounted as volumes.
    2. Verify `PYTHONPATH` includes the scripts directory.
    3. Check `beads_manager.py` for absolute host paths vs container paths.

## 6. Next.js 404 Errors
- **Symptom:** Playwright tests fail with 404 on `/chat` or `/health`.
- **Cause:** Stale GHCR image or failed build.
- **Resolution:**
    1. Force a local build: Switch `image:` to `build:` in `docker-compose.yml`.
    2. Run `docker-compose up -d --build`.

## 7. Prod Engine Showing Stale Data / Wrong Weather
- **Symptom:** `game_info` shows raw IDs, weather always 72°F/5mph, engine behaviour differs from dev.
- **Cause:** `betting-prod/docker-compose.yml` was using `image: ghcr.io/grantbest/betting-application/engine:main` — a stale GHCR image with an outdated `WeatherService` that hits `api.weatherprovider.com` (non-existent).
- **Resolution (applied 2026-03-19):** Changed engine in `betting-prod/docker-compose.yml` to `build: context: ../../../BettingApp`. Both prod and dev now build the engine from local source. Do NOT revert to the GHCR image.

## 8. `game_info` NULL in `bet_tracking`
- **Symptom:** Dashboard shows `ID: 745201` instead of game names.
- **Cause:** `init_db.py` seed INSERT omitted the `game_info` column.
- **Resolution (applied 2026-03-19):** `init_db.py` updated to include `game_info` (with weather strings) in the seed INSERT. Any existing NULL rows must be backfilled manually:
    ```bash
    docker exec betting-prod-engine python3 -c "
    import psycopg2, os
    conn = psycopg2.connect(host='postgres', dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'))
    cur = conn.cursor()
    cur.execute(\"UPDATE bet_tracking SET game_info = 'Team Vs Team - M/D | 🌡️ X°F | 💨 Xmph' WHERE game_id = <id>\")
    conn.commit()
    "
    ```
