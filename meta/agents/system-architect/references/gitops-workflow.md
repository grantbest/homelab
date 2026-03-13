# GitOps CI/CD Workflow Vision

## The Standard Pipeline

1.  **Code Change:** A developer pushes code to a branch (`dev` or `main`).
2.  **Build Phase:** A GitHub Action (or similar CI runner) builds the Docker image.
3.  **Registry Phase:** The image is pushed to a secure registry (e.g., GHCR).
4.  **Manifest Update:** The deployment repository (Homelab) is updated with the new image tag.
5.  **Synchronization Phase:** A GitOps controller (or webhook-triggered pull) syncs the homelab infrastructure to match the manifests in Git.
6.  **Health Check:** Post-deployment validation confirms service health.

## Core Rules

- **Immutable Infrastructure:** Containers are never patched; they are always replaced with a new version.
- **Config as Code:** All environment-specific configurations (.env, secrets) are managed via Git (using SOPS for encryption).
- **Separation of Concerns:** Application code and infrastructure code live in separate repositories or distinct directories.
