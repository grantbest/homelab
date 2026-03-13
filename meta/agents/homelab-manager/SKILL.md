---
name: homelab-manager
description: Manage homelab infrastructure (Traefik, Docker, Postgres, Redis, SOPS). Use for infra updates, troubleshooting routing, secret management, or adding new shared services.
---

# homelab-manager

Expert guide for maintaining and evolving the BestFam Homelab infrastructure.

## Core Workflows

### 1. Infrastructure Management
- Use Docker Compose for all service orchestration.
- Prioritize **Immutable Infrastructure**: always recreate containers on change.
- Reference [references/architecture.md](references/architecture.md) for the current layout.

### 2. Secret Management (SOPS)
- All secrets must be encrypted using SOPS + Age.
- Follow the workflow in [references/sops-workflow.md](references/sops-workflow.md) for decryption/encryption during changes.
- Ensure `SOPS_AGE_KEY_FILE` is always set before operations.

### 3. Health & Validation
- After any change, run [scripts/validate_health.sh](scripts/validate_health.sh) to verify core services.
- Check Traefik routing at `localhost:8080/api/http/routers`.

## Core Principles
- **GitOps First:** Infrastructure state lives in the `Homelab/` directory.
- **Isolation:** Strictly separate shared services from application-specific apps.
