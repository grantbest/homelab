import os
import json
import asyncio
import time
from fastapi import FastAPI, Request
from temporalio.client import Client
import uvicorn
import sys

# Add scripts to path for beads_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../BestFam-Orchestrator/scripts")))
from beads_manager import read_bead

app = FastAPI()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")

async def get_temporal_client():
    return await Client.connect(TEMPORAL_ADDRESS)

def _is_epic(title: str) -> bool:
    t = title.upper()
    return "[EPIC]" in t or t.startswith("EPIC:") or t.startswith("EPIC ")

@app.post("/vikunja")
async def vikunja_webhook(request: Request):
    payload = await request.json()
    event = payload.get("event_name")
    data = payload.get("data", {})
    task = data.get("task", {})
    task_id = str(task.get("id"))

    if not task_id:
        return {"status": "ignored", "reason": "No task ID"}

    # 1. Ignore agent actions
    if event == "task.comment.created":
        content = data.get("comment", {}).get("comment", "")
        if "[AGENT_SIGNATURE]" in content:
            return {"status": "ignored", "reason": "Agent comment"}
    
    # 2. Extract Bucket Title
    buckets = task.get("buckets", [])
    bucket_title = buckets[0].get("title") if buckets else "Inbox"
    
    # 3. Resolve Intent
    # We map bucket entry to a specific specialized workflow
    # This decouples the bucket name from the monolithic MayorWorkflow
    
    intent = None
    workflow_name = None
    
    if bucket_title == "Design" and event == "task.updated":
        intent = "DESIGN"
        workflow_name = "DesignWorkflow"
    elif bucket_title == "Design" and event == "task.comment.created":
        intent = "REFINE"
        workflow_name = "MayorWorkflow" # Keep DesignRefine in Mayor for now
    elif bucket_title == "Doing" and event == "task.updated":
        # Resolve if this is a breakdown (Epic) or implementation (Story)
        bead = read_bead(task_id)
        if _is_epic(bead['title']):
            intent = "BREAKDOWN"
            workflow_name = "BreakdownWorkflow"
        else:
            intent = "IMPLEMENT"
            workflow_name = "ImplementationWorkflow"
    elif bucket_title == "Validation" and event == "task.updated":
        intent = "VALIDATE"
        workflow_name = "RefineryWorkflow"

    if not intent or not workflow_name:
        return {"status": "ignored", "bucket": bucket_title, "event": event}

    # 4. Anti-Loop & Deduplication
    # We use a deterministic workflow ID based on the task and intent
    workflow_id = f"agile-task-{task_id}-{intent.lower()}"
    
    try:
        client = await get_temporal_client()
        
        args = [task_id]
        if intent == "REFINE":
            comment_text = data.get("comment", {}).get("comment", "")
            args = [task_id, "DesignRefine", comment_text]
        
        await client.start_workflow(
            workflow_name,
            args=args,
            id=workflow_id,
            task_queue="modular-orchestrator-queue",
        )
        
        print(f"DISPATCHER: Started {workflow_name} for Task {task_id} (Intent: {intent})")
        return {"status": "triggered", "workflow": workflow_name, "id": workflow_id}

    except Exception as e:
        if "already" in str(e).lower() or "exists" in str(e).lower():
            print(f"DISPATCHER: Task {task_id} already processing intent {intent}. Skipping.")
            return {"status": "skipped", "reason": "already running"}
        
        print(f"DISPATCHER ERROR: {e}")
        return {"status": "error", "reason": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
