import asyncio
from temporalio.client import Client
from unified_worker import DeploymentHealthWorkflow
from beads_manager import create_bead
import sys

async def trigger_deployment_check():
    # 1. Create a Bead for the new deployment
    bead_id = create_bead(
        title="Deployment Verification: Betting App v1.2.0",
        description="Verifying deployment health and accessibility.",
        requesting_agent="CI/CD Pipeline"
    )
    print(f"Deployment Bead Created: {bead_id}")

    # 2. Connect to Temporal
    client = await Client.connect("localhost:7233")
    
    # 3. Start the Workflow
    print(f"Triggering DeploymentHealthWorkflow for bead {bead_id}...")
    result = await client.execute_workflow(
        DeploymentHealthWorkflow.run,
        bead_id,
        id=f"deploy-verify-{bead_id}",
        task_queue="main-orchestrator-queue"
    )
    
    print(f"Workflow Final Result: {result}")

if __name__ == "__main__":
    asyncio.run(trigger_deployment_check())
