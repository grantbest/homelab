---
name: system-architect
description: Requirements and system architecture for microservices and GitOps. Use when analyzing requirements, designing service boundaries, drafting architectural blueprints (SOLUTION.md), or planning CI/CD pipelines.
---

# system-architect

Expert guide for designing modular, simple, and clean microservice architectures following GitOps principles.

## Core Workflows

### 1. Requirements Analysis
- Analyze user requests for core entities and service boundaries.
- Enforce **Object-Oriented Data** and **Normalization** (3NF) in database design.
- Reference the core design principles in [references/manifesto.md](references/manifesto.md).

### 2. Architectural Blueprinting
- Generate a `SOLUTION.md` for new projects using the standardized [assets/SOLUTION_TEMPLATE.md](assets/SOLUTION_TEMPLATE.md).
- Ensure every service has a single, well-defined responsibility.
- Define explicit and stable interface boundaries between services.

### 3. CI/CD and Pipeline Planning
- Propose a consistent **GitOps** pipeline for all infrastructure and app changes.
- Follow the workflow vision outlined in [references/gitops-workflow.md](references/gitops-workflow.md).
- Prioritize environment isolation (Dev, Staging, Prod).

## Design Constraints
- **Simplicity over Complexity:** If a solution is over-engineered, suggest a simpler alternative.
- **Microservices Boundary:** Ensure services are decoupled but highly cohesive.
- **Immutable Infrastructure:** Containers must be replaced, not patched.
