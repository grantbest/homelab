import asyncio
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from beads_manager import update_bead, read_bead

# --- Shared Activities ---

@activity.defn
async def execute_bead_activity(bead_id: str) -> str:
    print(f"Agent starting work on bead: {bead_id}")
    update_bead(bead_id, {"status": "in_progress"})
    
    # Simulate processing
    await asyncio.sleep(2)
    
    update_bead(bead_id, {
        "status": "completed",
        "resolution": "Simulated task completion by agent."
    })
    return f"Bead {bead_id} processed successfully."

@activity.defn
async def check_betting_app_health(bead_id: str) -> bool:
    print(f"Checking Betting App health for bead: {bead_id}")
    update_bead(bead_id, {"status": "in_progress", "context": {"step": "health_check"}})
    
    # Simulate health check. We simulate a failure to trigger the Homelab agent handoff.
    await asyncio.sleep(2)
    app_status = "unhealthy" 
    error_msg = "Frontend (port 3001) is not responding. Possible Traefik or Network issue."
    
    update_bead(bead_id, {
        "context": {"app_health": app_status, "error": error_msg},
        "description": f"Health Check Failed: {error_msg}. Requesting Infra Audit."
    })
    return False

@activity.defn
async def audit_homelab_infrastructure(bead_id: str) -> str:
    print(f"Auditing Homelab infrastructure for bead: {bead_id}")
    update_bead(bead_id, {"status": "in_progress", "context": {"step": "infra_audit"}})
    
    # Simulate auditing Traefik/Docker
    await asyncio.sleep(2)
    audit_results = "Traefik is running, but service 'betting-frontend' is missing labels for 'bestfam.us'."
    fix_applied = "Added missing Traefik routing labels to BettingApp docker-compose."
    
    update_bead(bead_id, {
        "status": "completed",
        "context": {"audit": audit_results, "fix": fix_applied},
        "resolution": f"Infrastructure issue fixed: {fix_applied}"
    })
    return "Fix applied successfully."

# --- Workflows ---

@workflow.defn
class AgenticTroubleshootWorkflow:
    @workflow.run
    async def run(self, domain: str, bead_id: str) -> str:
        task_queue = "homelab-queue" if domain == "homelab" else "betting-app-queue"
        result = await workflow.execute_activity(
            "execute_bead_activity",
            bead_id,
            start_to_close_timeout=timedelta(minutes=5),
            task_queue=task_queue
        )
        return result

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

async def main():
    client = await Client.connect("localhost:7233")
    
    # Common activities and workflows
    activities = [execute_bead_activity, check_betting_app_health, audit_homelab_infrastructure]
    workflows = [AgenticTroubleshootWorkflow, DeploymentHealthWorkflow]
    
    # We start workers on multiple queues to handle all tasks
    queues = ["main-orchestrator-queue", "homelab-queue", "betting-app-queue"]
    workers = []
    
    for queue in queues:
        worker = Worker(
            client,
            task_queue=queue,
            activities=activities,
            workflows=workflows,
        )
        workers.append(worker.run())
        print(f"Worker started for queue: {queue}")
    
    await asyncio.gather(*workers)

if __name__ == "__main__":
    asyncio.run(main())
