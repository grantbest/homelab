import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.client import Client

# We define the Workflow inside the script for simplicity
@workflow.defn
class AgenticTroubleshootWorkflow:
    @workflow.run
    async def run(self, domain: str, bead_id: str) -> str:
        # Determine the target queue based on the domain
        task_queue = "homelab-queue" if domain == "homelab" else "betting-app-queue"
        
        # Execute the activity on the targeted agent worker
        # Note: We use string reference here to avoid circular imports 
        # as workers run the actual code.
        result = await workflow.execute_activity(
            "execute_bead_activity",
            bead_id,
            start_to_close_timeout=timedelta(minutes=5),
            task_queue=task_queue
        )
        return result

async def trigger_troubleshoot(domain, bead_id):
    client = await Client.connect("localhost:7233")
    
    # Start the workflow
    handle = await client.start_workflow(
        AgenticTroubleshootWorkflow.run,
        args=[domain, bead_id],
        id=f"troubleshoot-{bead_id}",
        task_queue="main-orchestrator-queue"
    )
    
    print(f"Workflow started. ID: {handle.id}")
    result = await handle.result()
    print(f"Workflow finished. Result: {result}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        asyncio.run(trigger_troubleshoot(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: python3 central_orchestrator.py <domain> <bead_id>")
