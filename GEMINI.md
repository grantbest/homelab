# Homelab Architecture Documentation (Staged)

This document describes the current state of the `bestfam.us` homelab architecture.

## 1. High-Level Traffic Flow

### A. Public Access (Cloudflare Tunnel + Access)
1.  **Internet User** -> `https://dev.bestfam.us` (Cloudflare Edge).
2.  **Cloudflare Access (Bouncer)** -> Challenges user for login (OTP or Identity Provider).
3.  **Cloudflare Edge** -> **Cloudflare Tunnel** (Encrypted) - *Only if authenticated*.
4.  **cloudflared (Container)** -> **Traefik (Container:80)** (HTTP).
5.  **Traefik** -> **App Router** (Docker or Host).

---

## 2. Shared Services (`shared-services/`)

Core infrastructure that runs continuously and serves multiple applications.

*   **Network**: `homelab_global` (Docker Bridge).
*   **Services**:
    *   **Traefik**: Reverse proxy with ACME (SSL) and Docker service discovery.
    *   **Cloudflared**: Secure tunnel to Cloudflare Edge.
    *   **Postgres**: Centralized database for all apps.
    *   **Redis**: Centralized cache for all apps.

---

## 3. Application Stack (`apps/`)

### **Betting Engine** (`apps/betting-engine/`)
*   **Dashboard**: WE do it inc. dashboard, routed to `bestfam.us`.
*   **Engine**: Backend betting engine logic.
*   **Connection**: Uses `homelab_global` to reach `postgres` and `redis`.

---

## 4. Security & Secrets

### **Identity & Access Management (Cloudflare Access)**
*   **Status**: Active for `dev.bestfam.us`, `traefik.bestfam.us`, and `whoami.bestfam.us`.

### **Secrets Management (Tier 2: SOPS + AGE)**
*   **Mechanism**: All `.env` files (in `shared-services/` and `apps/`) are encrypted via **SOPS**.
*   **Key**: `~/.sops_age_key.txt`.

---

## 5. Automated Validation & Pipeline (GitOps)

The `pipeline.sh` script is the "Orchestrator" for the entire environment. It performs:
1.  **Secret Decryption**: Unlocks `.env` files.
2.  **App Build**: Navigates to the source code on the MacBook and builds production images.
3.  **Security Scan**: Runs **Trivy** on new images and **Gitleaks** on the codebase.
4.  **Deployment**: Restarts containers with the latest configuration and images.
5.  **Smoke Test**: Checks infrastructure health via `tests/validate-homelab.sh`.
6.  **Regression Test**: Executes **Playwright** UI tests to verify business logic.

To trigger locally:
```bash
./pipeline.sh
```

To trigger via Git:
Simply `git push` to the `main` branch. The **GitHub Actions Runner** will execute the pipeline.

---

## 6. Current Component Inventory

| Service | Domain | Internal Target | Auth Protection | Network |
| :--- | :--- | :--- | :--- | :--- |
| **Prod Web App** | `bestfam.us` | `betting-dashboard:3000` | Public / WAF | `homelab_global` |
| **Dev Web App** | `dev.bestfam.us` | `host.docker.internal:3000`| **Cloudflare Access** | `homelab_global` |
| **Traefik Dashboard** | `traefik.bestfam.us`| `api@internal` | **Cloudflare Access** | `homelab_global` |
---

## 7. Agentic Orchestration Protocol

This project is part of a centralized multi-agent system using **Temporal** and **Beads**.

### **The "Command Center" Rule**
- **Orchestration:** All multi-agent workflows are managed from this directory.
- **Durable Execution:** The `unified_worker.py` (located at `../../unified_worker.py` or centrally) must be running to process tasks from the `main-orchestrator-queue` and `homelab-queue`.
- **State Management:** Use `scripts/beads_manager.py` to create, read, and update task state in the `.beads/` directory.

### **Agent Directives**
1. **Check Beads First:** Before starting a task, always run `python3 scripts/beads_manager.py list` to see if there are pending handoffs from other agents (e.g., the Betting App agent).
2. **Respect the Handoff:** If a task involves application-level fixes (Betting App logic), do NOT attempt to fix it here. Update the Bead and allow the Central Orchestrator to route it to the appropriate worker.
3. **Log Everything:** Ensure all infrastructure audits and fixes are recorded in the `resolution` field of the Bead.

