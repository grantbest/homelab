import os
import json
import uuid
import httpx
from datetime import datetime
from pathlib import Path

# Configuration from Environment
VIKUNJA_BASE_URL = os.getenv("VIKUNJA_BASE_URL", "https://tracker.bestfam.us/api/v1")
VIKUNJA_API_TOKEN = os.getenv("VIKUNJA_API_TOKEN")
VIKUNJA_PROJECT_ID = os.getenv("VIKUNJA_PROJECT_ID", "2")

def get_headers():
    return {
        "Authorization": f"Bearer {VIKUNJA_API_TOKEN}",
        "Content-Type": "application/json"
    }

def create_bead(title, description, requesting_agent, assigned_agent=None):
    """Creates a new bead as a Vikunja task."""
    if not VIKUNJA_API_TOKEN:
        print("Vikunja API Token not set. Falling back to local file (legacy).")
        return create_legacy_bead(title, description, requesting_agent, assigned_agent)

    url = f"{VIKUNJA_BASE_URL}/projects/{VIKUNJA_PROJECT_ID}/tasks"
    
    payload = {
        "title": title,
        "description": f"{description}\n\n--- AGENT METADATA ---\n" + json.dumps({
            "requesting_agent": requesting_agent,
            "assigned_agent": assigned_agent,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }, indent=2)
    }
    
    try:
        with httpx.Client() as client:
            response = client.put(url, headers=get_headers(), json=payload)
            response.raise_for_status()
            task = response.json()
            bead_id = str(task['id'])
            ui_index = str(task['index'])
            print(f"Created Vikunja bead: #{ui_index} (Internal ID: {bead_id})")
            return bead_id # We still return ID for internal API robustness
    except Exception as e:
        print(f"Failed to create Vikunja task: {e}")
        return create_legacy_bead(title, description, requesting_agent, assigned_agent)

def read_bead(bead_id):
    """Reads a bead from Vikunja. Supports both ID and UI Index (#)."""
    if not str(bead_id).isdigit():
        return read_legacy_bead(bead_id)

    # If the ID is small (like 50), it might be an index. 
    # But since IDs also start small, we'll try ID first, then Index.
    url = f"{VIKUNJA_BASE_URL}/tasks/{bead_id}"
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=get_headers())
            if response.status_code == 404:
                # Try looking up by index if ID not found
                idx_url = f"{VIKUNJA_BASE_URL}/projects/{VIKUNJA_PROJECT_ID}/tasks?filter=index%20%3D%20{bead_id}"
                response = client.get(idx_url, headers=get_headers())
                response.raise_for_status()
                tasks = response.json()
                if not tasks: raise FileNotFoundError()
                task = tasks[0]
            else:
                response.raise_for_status()
                task = response.json()
            
            desc_parts = task.get("description", "").split("--- AGENT METADATA ---")
            metadata = {}
            clean_desc = task.get("description", "")
            if len(desc_parts) > 1:
                try:
                    metadata = json.loads(desc_parts[1].strip())
                    clean_desc = desc_parts[0].strip()
                except Exception:
                    pass
            
            return {
                "id": str(task['id']),
                "index": str(task['index']),
                "title": task['title'],
                "description": clean_desc,
                "status": metadata.get("status", "pending"),
                "requesting_agent": metadata.get("requesting_agent"),
                "assigned_agent": metadata.get("assigned_agent"),
                "created_at": metadata.get("created_at"),
                "updated_at": task.get("updated"),
                "context": metadata.get("context", {}),
                "resolution": metadata.get("resolution")
            }
    except Exception as e:
        print(f"Failed to read Vikunja task {bead_id}: {e}")
        raise FileNotFoundError(f"Bead {bead_id} not found in Vikunja.")

def update_bead(bead_id, updates):
    """Updates a bead in Vikunja."""
    if not str(bead_id).isdigit():
        return update_legacy_bead(bead_id, updates)

    current = read_bead(bead_id)
    # Ensure we use the actual Internal ID for the update POST
    internal_id = current['id']
    ui_index = current['index']
    
    status = updates.get("status", current.get("status"))
    resolution = updates.get("resolution", current.get("resolution"))
    context = current.get("context", {})
    if "context" in updates:
        context.update(updates["context"])
    
    new_metadata = {
        "requesting_agent": current.get("requesting_agent"),
        "assigned_agent": current.get("assigned_agent"),
        "created_at": current.get("created_at"),
        "status": status,
        "resolution": resolution,
        "context": context
    }
    
    url = f"{VIKUNJA_BASE_URL}/tasks/{internal_id}"
    payload = {
        "title": updates.get("title", current.get("title")),
        "description": f"{updates.get('description', current.get('description'))}\n\n--- AGENT METADATA ---\n" + json.dumps(new_metadata, indent=2)
    }
    
    # Explicitly handle the 'done' state
    if "done" in updates:
        payload["done"] = updates["done"]
    elif status == "completed":
        payload["done"] = True
    else:
        # Default to False for all other active states
        payload["done"] = False

    try:
        with httpx.Client() as client:
            response = client.post(url, headers=get_headers(), json=payload)
            response.raise_for_status()
            print(f"Updated Vikunja bead: #{ui_index} (Internal ID: {internal_id})")
            return read_bead(internal_id)
    except Exception as e:
        print(f"Failed to update Vikunja task {internal_id}: {e}")
        return update_legacy_bead(internal_id, updates)

def list_beads(status=None):
    if not VIKUNJA_API_TOKEN:
        return []
    
    url = f"{VIKUNJA_BASE_URL}/projects/{VIKUNJA_PROJECT_ID}/tasks"
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=get_headers())
            response.raise_for_status()
            tasks = response.json()
            
            beads = []
            for t in tasks:
                desc_parts = t.get("description", "").split("--- AGENT METADATA ---")
                metadata = {}
                if len(desc_parts) > 1:
                    try:
                        metadata = json.loads(desc_parts[1].strip())
                    except Exception:
                        pass
                
                bead = {
                    "id": str(t['id']),
                    "index": str(t['index']),
                    "title": t['title'],
                    "status": metadata.get("status", "pending"),
                    "requesting_agent": metadata.get("requesting_agent"),
                    "assigned_agent": metadata.get("assigned_agent")
                }
                
                if not status or bead["status"] == status:
                    beads.append(bead)
            
            return beads
    except Exception as e:
        print(f"Failed to list tasks: {e}")
        return []

# --- Legacy Support ---
def get_beads_dirs():
    # Supports both container paths and host paths for dev
    paths = [
        Path("/app/Homelab/.beads"),
        Path("/app/BettingApp/.beads"),
        Path("/Users/grantbest/Documents/Active/Homelab/.beads"),
        Path("/Users/grantbest/Documents/Active/BettingApp/.beads"),
        Path("/Users/grantbest/Documents/Active/BestFam-Orchestrator/.beads"),
        Path(".beads")
    ]
    return [p for p in paths if p.exists() and p.is_dir()]

def create_legacy_bead(title, description, requesting_agent, assigned_agent=None):
    bead_id = str(uuid.uuid4())
    bead_data = {
        "id": bead_id, "title": title, "description": description, "status": "pending",
        "requesting_agent": requesting_agent, "assigned_agent": assigned_agent,
        "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat(),
        "context": {}, "resolution": None
    }
    dirs = get_beads_dirs()
    file_path = (dirs[0] if dirs else Path(".beads")) / f"{bead_id}.json"
    with open(file_path, "w") as f: json.dump(bead_data, f, indent=4)
    print(f"Created legacy bead: {bead_id}")
    return bead_id

def read_legacy_bead(bead_id):
    for directory in get_beads_dirs():
        file_path = directory / f"{bead_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f: return json.load(f)
    raise FileNotFoundError(f"Legacy bead {bead_id} not found.")

def update_legacy_bead(bead_id, updates):
    for directory in get_beads_dirs():
        file_path = directory / f"{bead_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f: data = json.load(f)
            data.update(updates)
            data["updated_at"] = datetime.utcnow().isoformat()
            with open(file_path, "w") as f: json.dump(data, f, indent=4)
            print(f"Updated legacy bead: {bead_id}")
            return data
    raise FileNotFoundError(f"Legacy bead {bead_id} not found.")

def upload_attachment(bead_id, file_path):
    """Uploads a file as an attachment to a Vikunja task."""
    if not str(bead_id).isdigit() or not os.path.exists(file_path):
        return

    try:
        # Resolve ID if Index provided
        bead = read_bead(bead_id)
        internal_id = bead['id']
        ui_index = bead['index']
        
        url = f"{VIKUNJA_BASE_URL}/tasks/{internal_id}/attachments"
        headers = {"Authorization": f"Bearer {VIKUNJA_API_TOKEN}"}
        
        with open(file_path, "rb") as f:
            files = {"files": (os.path.basename(file_path), f)}
            with httpx.Client() as client:
                response = client.put(url, headers=headers, files=files)
                response.raise_for_status()
                print(f"Uploaded attachment {file_path} to Vikunja bead: #{ui_index} (Internal ID: {internal_id})")
    except Exception as e:
        print(f"Failed to upload attachment: {e}")

def add_comment(bead_id, comment_text):
    """Adds a comment to a Vikunja task with an AGENT signature."""
    if not str(bead_id).isdigit():
        return

    try:
        # Resolve ID if Index provided
        bead = read_bead(bead_id)
        internal_id = bead['id']
        ui_index = bead['index']

        signed_comment = f"{comment_text}\n\n[AGENT_SIGNATURE]"
        url = f"{VIKUNJA_BASE_URL}/tasks/{internal_id}/comments"
        headers = {
            "Authorization": f"Bearer {VIKUNJA_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {"comment": signed_comment}
        
        with httpx.Client() as client:
            response = client.put(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Added comment to Vikunja bead: #{ui_index} (Internal ID: {internal_id})")
    except Exception as e:
        print(f"Failed to add comment: {e}")

def get_bucket_id(bucket_name: str):
    """Returns the Vikunja bucket ID matching the given name via the Kanban view."""
    VIKUNJA_KANBAN_VIEW_ID = os.getenv("VIKUNJA_KANBAN_VIEW_ID", "8")
    url = f"{VIKUNJA_BASE_URL}/projects/{VIKUNJA_PROJECT_ID}/views/{VIKUNJA_KANBAN_VIEW_ID}/buckets"
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=get_headers())
            response.raise_for_status()
            for bucket in response.json():
                if bucket.get("title", "").lower() == bucket_name.lower():
                    return bucket["id"]
    except Exception as e:
        print(f"Failed to get bucket ID for '{bucket_name}': {e}")
    return None

def move_to_bucket(bead_id: str, bucket_name: str):
    """Moves a Vikunja task to the named bucket (Kanban column)."""
    bucket_id = get_bucket_id(bucket_name)
    if not bucket_id:
        print(f"Bucket '{bucket_name}' not found in project {VIKUNJA_PROJECT_ID}.")
        return
    bead = read_bead(bead_id)
    internal_id = bead["id"]
    url = f"{VIKUNJA_BASE_URL}/tasks/{internal_id}"
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=get_headers(), json={"bucket_id": bucket_id})
            response.raise_for_status()
            print(f"Moved bead #{bead['index']} to bucket '{bucket_name}'")
    except Exception as e:
        print(f"Failed to move bead {bead_id} to bucket '{bucket_name}': {e}")

def link_beads(parent_id, child_id, relation_kind="subtask"):
    """Creates a relationship between two Vikunja tasks."""
    if not str(parent_id).isdigit() or not str(child_id).isdigit():
        return

    try:
        # Resolve IDs
        p_bead = read_bead(parent_id)
        c_bead = read_bead(child_id)
        
        url = f"{VIKUNJA_BASE_URL}/tasks/{p_bead['id']}/relations"
        headers = {
            "Authorization": f"Bearer {VIKUNJA_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "other_task_id": int(c_bead['id']),
            "relation_kind": relation_kind
        }
        
        with httpx.Client() as client:
            response = client.put(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Linked bead #{c_bead['index']} to #{p_bead['index']} as {relation_kind}")
    except Exception as e:
        print(f"Failed to link beads: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for b in list_beads():
            print(f"[{b['status'].upper()}] {b['id']}: {b['title']}")
