import asyncio
import os
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from beads_manager import update_bead, read_bead

# --- AI Quarterback Activities ---

@activity.defn
async def analyze_bead_with_llm(bead_id: str) -> str:
    """
    Uses local Ollama to triage the bead and decide which sub-agent should handle it.
    """
    import ollama
    import json
    
    bead_data = read_bead(bead_id)
    description = bead_data.get("description", "")
    title = bead_data.get("title", "")
    
    # Ollama configuration
    # Default to localhost:11434 when running on the host
    ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3:latest")
    client = ollama.Client(host=ollama_host)
    
    system_prompt = (
        "You are the 'AI Quarterback', a central orchestrator for a microservices system. "
        "Your job is to read a task description and route it to the correct sub-agent queue.\n\n"
        "Available Queues:\n"
        "1. 'homelab-queue': Infrastructure, Docker, Traefik, networking, CI/CD, and hardware issues.\n"
        "2. 'betting-app-queue': Application code (Next.js, Python), database schemas, sports logic, and bug fixes.\n\n"
        "Respond ONLY with a JSON object containing two fields:\n"
        "- 'queue': The target queue name (one of the above).\n"
        "- 'reasoning': A brief 1-sentence explanation of why you chose this queue."
    )
    
    user_prompt = f"Task Title: {title}\nTask Description: {description}"
    
    try:
        response = client.chat(model=model, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ])
        content = response['message']['content'].strip()
        
        # Clean up possible Markdown code blocks if LLM included them
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse and validate the response
        result = json.loads(content)
        target_queue = result.get("queue")
        reasoning = result.get("reasoning", "No reasoning provided.")
        
        if target_queue not in ["homelab-queue", "betting-app-queue"]:
            raise ValueError(f"Invalid queue suggested by AI: {target_queue}")
            
        print(f"AI Triage Result: {target_queue} (Reason: {reasoning})")
        
        # Update bead with AI's decision
        update_bead(bead_id, {
            "context": {
                "triage_queue": target_queue,
                "triage_reasoning": reasoning
            }
        })
        
        return target_queue
        
    except Exception as e:
        print(f"AI Triage Failed: {e}")
        # Default to homelab-queue as a fallback if triage fails
        return "homelab-queue"

# --- Quarterback Workflows ---

@workflow.defn
class TriageWorkflow:
    @workflow.run
    async def run(self, bead_id: str) -> str:
        # 1. Ask the AI which queue should handle this
        target_queue = await workflow.execute_activity(
            analyze_bead_with_llm,
            bead_id,
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # 2. Dispatch the actual work to that queue
        # Note: We use string-based Activity names to avoid importing the sub-agents directly
        result = await workflow.execute_activity(
            "execute_bead_activity",
            bead_id,
            start_to_close_timeout=timedelta(minutes=10),
            task_queue=target_queue
        )
        
        return f"Task routed to {target_queue} and completed: {result}"

# --- Worker ---

async def main():
    # Connect to the local Temporal server
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)
    
    # Run the worker for the 'main-orchestrator-queue'
    worker = Worker(
        client,
        task_queue="main-orchestrator-queue",
        activities=[analyze_bead_with_llm],
        workflows=[TriageWorkflow],
    )
    print("AI Quarterback Worker started on 'main-orchestrator-queue'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
