---
name: betting-app-manager
description: Manage BettingApp codebase (engine logic, rules, frontend, 3NF data models). Use for adding rules, fixing engine bugs, UI updates, or database schema changes.
---

# betting-app-manager

Expert guide for the BettingApp lifecycle, focusing on quantitative analytics and AI-driven insights.

## Core Workflows

### 1. Betting Engine Logic
- Maintain the `engine.py` core logic.
- Ensure all betting triggers use the JSON-based `RuleEvaluator`.
- Enforce the **Kelly Criterion** for all stake calculations.

### 2. Data Integrity (3NF)
- All schema changes must follow 3rd Normal Form (3NF).
- Reference [references/data-model.md](references/data-model.md) for the authoritative schema.
- Use `init_db.py` for automated migrations/seeding.

### 3. Rules Engine Management
- All betting strategies must be defined as JSON rules.
- Reference [references/rule-schema.md](references/rule-schema.md) for the JSON structure.
- Statuses: `ACTIVE` (alerts on), `DRY_RUN` (logs only), `INACTIVE` (disabled).

## Core Principles
- **Modularity:** Keep analytics logic decoupled from ingestion.
- **Environment Aware:** Ensure `APP_ENV` strictly controls demo data seeding.
