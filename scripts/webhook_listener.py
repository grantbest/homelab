import os
import json
import asyncio
import time
from fastapi import FastAPI, Request
from temporalio.client import Client
import uvicorn

app = FastAPI()

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")

async def get_temporal_client():
    return await Client.connect(TEMPORAL_ADDRESS)

@app.post("/vikunja")
async def vikunja_webhook(request: Request):
    payload = await request.json()
    event = payload.get("event_name")
    data = payload.get("data", {})
    task = data.get("task", {})
    task_id = task.get("id")

    # Extract Bucket Title
    buckets = task.get("buckets", [])
    bucket_title = buckets[0].get("title") if buckets else "Inbox"

    # 1. ANTI-LOOP FILTER — only block agent-driven updates while still in Design
    # If the user moves the task to a different bucket, always let it through.
    description = task.get("description", "")
    if "[AGENT_SIGNATURE]" in description or "## Solution Design" in description:
        if event == "task.updated" and bucket_title == "Design":
            print(f"WEBHOOK: Ignoring agent-driven update for Task {task_id}")
            return {"status": "ignored", "reason": "Agent signature detected in description"}

    # 2. Ignore agent comments
    if event == "task.comment.created":
        content = data.get("comment", {}).get("comment", "")
        if "[AGENT_SIGNATURE]" in content:
            return {"status": "ignored", "reason": "Agent comment detected"}

    # Normalize bucket names to internal workflow names
    # To-Do is the backlog — no trigger needed
    BUCKET_MAP = {
        "Design": "Design",
        "Doing": "Doing",
        "Validation": "Validation",
    }
    workflow_bucket = BUCKET_MAP.get(bucket_title)

    print(f"WEBHOOK: Event '{event}' for Task {task_id} in bucket '{bucket_title}' -> {workflow_bucket or 'ignored'}")

    if event not in ["task.updated", "task.comment.created"] or workflow_bucket is None:
        return {"status": "ignored"}

    try:
        client = await get_temporal_client()

        # For user comment replies in Design: pass the comment so Mayor can do a targeted refine
        # instead of re-running the full design pipeline.
        if event == "task.comment.created" and workflow_bucket == "Design":
            comment_text = data.get("comment", {}).get("comment", "")
            workflow_id = f"agile-task-{task_id}-design-refine-{int(time.time())}"
            await client.start_workflow(
                "MayorWorkflow",
                [str(task_id), "DesignRefine", comment_text],
                id=workflow_id,
                task_queue="main-orchestrator-queue",
            )
            print(f"SUCCESS: Triggered design refine {workflow_id}")
            return {"status": "triggered", "workflow": workflow_id}

        # Bucket entry (task.updated = bucket move) — deterministic ID, skip if already ran.
        # Never use timestamp fallback for bucket moves — link_beads fires task.updated on the
        # parent epic, and a timestamp fallback would re-trigger breakdown, creating a loop.
        workflow_id = f"agile-task-{task_id}-{workflow_bucket.lower()}-entry"
        try:
            await client.start_workflow(
                "MayorWorkflow",
                [str(task_id), workflow_bucket],
                id=workflow_id,
                task_queue="main-orchestrator-queue",
            )
        except Exception as e:
            if "already" in str(e).lower() or "exists" in str(e).lower():
                print(f"WEBHOOK: Workflow {workflow_id} already ran — skipping duplicate trigger")
                return {"status": "skipped", "reason": "workflow already ran for this bucket entry"}
            raise

        print(f"SUCCESS: Triggered {workflow_id}")
        return {"status": "triggered", "workflow": workflow_id}

    except Exception as e:
        return {"status": "error", "reason": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
