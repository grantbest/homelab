import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
import json
import subprocess
from pathlib import Path
from datetime import datetime

# --- Logic from beads_manager (to avoid imports) ---
def get_beads_dir():
    return Path("/Users/grantbest/Documents/Active/Homelab/.beads") # Standardized base

def update_bead_local(bead_id, updates):
    # Try both directories
    paths = [
        Path("/Users/grantbest/Documents/Active/Homelab/.beads") / f"{bead_id}.json",
        Path("/Users/grantbest/Documents/Active/BettingApp/.beads") / f"{bead_id}.json"
    ]
    for file_path in paths:
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
            data.update(updates)
            data["updated_at"] = datetime.utcnow().isoformat()
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Updated bead: {bead_id}")
            return True
    return False

# --- Betting App Agent Activities ---
@activity.defn
async def check_betting_app_health(bead_id: str) -> bool:
    print(f"Checking Betting App health for bead: {bead_id}")
    update_bead_local(bead_id, {"status": "in_progress", "context": {"step": "health_check"}})
    
    # Simulate checking the frontend on port 3001
    try:
        # In a real scenario: subprocess.run(["curl", "-f", "http://localhost:3001/health"])
        # We'll simulate a 502 error to trigger the Homelab agent handoff
        app_status = "unhealthy" 
        error_msg = "Frontend (port 3001) is not responding. Possible Traefik or Network issue."
        
        update_bead_local(bead_id, {
            "context": {"app_health": app_status, "error": error_msg},
            "description": f"Health Check Failed: {error_msg}. Requesting Infra Audit."
        })
        return False
    except Exception as e:
        return False

# --- Homelab Agent Activities ---
@activity.defn
async def audit_homelab_infrastructure(bead_id: str) -> str:
    print(f"Auditing Homelab infrastructure for bead: {bead_id}")
    update_bead_local(bead_id, {"status": "in_progress", "context": {"step": "infra_audit"}})
    
    # Simulate auditing Traefik/Docker
    # In a real scenario: subprocess.run(["docker", "ps", "--filter", "name=traefik"])
    audit_results = "Traefik is running, but service 'betting-frontend' is missing labels for 'bestfam.us'."
    fix_applied = "Added missing Traefik routing labels to BettingApp docker-compose."
    
    update_bead_local(bead_id, {
        "status": "completed",
        "context": {"audit": audit_results, "fix": fix_applied},
        "resolution": f"Infrastructure issue fixed: {fix_applied}"
    })
    return "Fix applied successfully."

# --- Workflows ---
@workflow.defn
class DeploymentHealthWorkflow:
    @workflow.run
    async def run(self, bead_id: str) -> str:
        # 1. Betting Agent checks health
        is_healthy = await workflow.execute_activity(
            check_betting_app_health,
            bead_id,
            start_to_close_timeout=timedelta(minutes=2),
            task_queue="betting-app-queue"
        )
        
        if is_healthy:
            return "Deployment is Healthy."
        
        # 2. If unhealthy, hand off to Homelab Agent
        print("Health check failed. Orchestrating handoff to Homelab Agent...")
        await workflow.execute_activity(
            audit_homelab_infrastructure,
            bead_id,
            start_to_close_timeout=timedelta(minutes=5),
            task_queue="homelab-queue"
        )
        
        return "Infrastructure fix applied. Deployment verified."

# --- Worker ---
async def start_worker(queue, is_orchestrator=False):
    client = await Client.connect("localhost:7233")
    activities = [check_betting_app_health, audit_homelab_infrastructure]
    workflows = [DeploymentHealthWorkflow] if is_orchestrator else []
    
    worker = Worker(
        client,
        task_queue=queue,
        activities=activities,
        workflows=workflows
    )
    print(f"Unified Worker started on queue: {queue} (Orchestrator={is_orchestrator})")
    await worker.run()

if __name__ == "__main__":
    import sys
    queue = sys.argv[1] if len(sys.argv) > 1 else "homelab-queue"
    is_orch = "--orch" in sys.argv
    asyncio.run(start_worker(queue, is_orch))
