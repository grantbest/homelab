import asyncio
import sys
import os
from temporalio.client import Client

# Add scripts directory to path to find beads_manager
sys.path.append(os.path.join(os.path.dirname(__file__), "../scripts"))
from beads_manager import create_bead, read_bead

async def main():
    title = "Post-Deployment Audit"
    description = "Audit the environment for any regressions after the latest pipeline run. Focus on CSS alignment and frontend-backend connectivity."
    
    # 1. Trigger the bead
    print(f"Triggering Agentic Validation: {title}...")
    bead_id = create_bead(title, description, "pipeline-orchestrator")
    
    # 2. Start the workflow
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)
    
    try:
        print(f"Waiting for Agentic AI to confirm deployment (Bead: {bead_id})...")
        # We start the workflow and wait for it to complete
        result = await client.execute_workflow(
            "TriageWorkflow",
            bead_id,
            id=f"triage-{bead_id}",
            task_queue="main-orchestrator-queue"
        )
        
        # 3. Read final bead status
        bead_data = read_bead(bead_id)
        if bead_data.get("status") == "completed":
            print(f"\033[0;32m✅ AGENTIC VALIDATION PASSED: {bead_data.get('resolution')}\033[0m")
            sys.exit(0)
        else:
            print(f"\033[0;31m❌ AGENTIC VALIDATION FAILED: {bead_data.get('status')}\033[0m")
            sys.exit(1)
            
    except Exception as e:
        print(f"\033[0;31m❌ AGENTIC VALIDATION ERROR: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
