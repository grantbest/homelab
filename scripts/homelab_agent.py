import asyncio
import os
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker
from beads_manager import update_bead, read_bead

# --- Homelab Agent Activities ---

@activity.defn
async def audit_homelab_infrastructure(bead_id: str) -> str:
    print(f"Auditing Homelab infrastructure for bead: {bead_id}")
    update_bead(bead_id, {"status": "in_progress", "context": {"step": "infra_audit"}})
    
    # Simulate auditing Traefik/Docker
    # In a real scenario: subprocess.run(["docker", "ps", "--filter", "name=traefik"])
    audit_results = "Traefik is running, but service 'betting-frontend' is missing labels for 'bestfam.us'."
    fix_applied = "Added missing Traefik routing labels to BettingApp docker-compose."
    
    update_bead(bead_id, {
        "status": "completed",
        "context": {"audit": audit_results, "fix": fix_applied},
        "resolution": f"Infrastructure issue fixed: {fix_applied}"
    })
    return "Fix applied successfully."

@activity.defn
async def execute_bead_activity(bead_id: str) -> str:
    print(f"Homelab Agent starting work on bead: {bead_id}")
    
    # Update status to 'in_progress'
    update_bead(bead_id, {"status": "in_progress"})
    
    # In a real scenario, this is where the agent would 
    # perform its specialized domain logic (infrastructure, CI/CD, etc.).
    # For now, we simulate success.
    
    update_bead(bead_id, {
        "status": "completed",
        "resolution": "Simulated Homelab infrastructure task completion by agent."
    })
    
    return f"Bead {bead_id} processed by Homelab Agent successfully."

async def main():
    # Connect to the local Temporal server
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)
    
    # Run the worker for the 'homelab-queue'
    worker = Worker(
        client,
        task_queue="homelab-queue",
        activities=[audit_homelab_infrastructure, execute_bead_activity],
    )
    print("Homelab Agent Worker started on 'homelab-queue'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
