import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Identify the root of the project by looking for the .beads folder
def get_beads_dir():
    # Avoid .resolve() at module level as it breaks Temporal sandbox
    # Use absolute path if possible, or search relatively without resolve()
    try:
        # Try to find it relative to this file
        current_path = Path(__file__).parent.absolute()
    except:
        # Fallback for environments where __file__ might be weird
        current_path = Path(".").absolute()

    while current_path != current_path.parent:
        beads_path = current_path / '.beads'
        if beads_path.exists() and beads_path.is_dir():
            return beads_path
        current_path = current_path.parent
    
    # Final fallback: check common locations
    common_paths = [
        Path("/Users/grantbest/Documents/Active/Homelab/.beads"),
        Path("./.beads")
    ]
    for p in common_paths:
        if p.exists():
            return p
            
    raise FileNotFoundError("Could not find '.beads' directory. Please ensure it exists at the project root.")

def get_dirs():
    """Returns a list of directories where beads might be stored."""
    # Hardcoded known paths for this specific environment
    paths = [
        Path("/Users/grantbest/Documents/Active/Homelab/.beads"),
        Path("/Users/grantbest/Documents/Active/BettingApp/.beads")
    ]
    return [p for p in paths if p.exists()]

def create_bead(title, description, requesting_agent, assigned_agent=None):
    """Creates a new bead (task) as a JSON file in the Homelab directory by default."""
    bead_id = str(uuid.uuid4())
    bead_data = {
        "id": bead_id,
        "title": title,
        "description": description,
        "status": "pending",
        "requesting_agent": requesting_agent,
        "assigned_agent": assigned_agent,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "context": {},
        "resolution": None
    }
    
    # Default to Homelab for new beads
    file_path = Path("/Users/grantbest/Documents/Active/Homelab/.beads") / f"{bead_id}.json"
    with open(file_path, "w") as f:
        json.dump(bead_data, f, indent=4)
    print(f"Created bead: {bead_id}")
    return bead_id

def read_bead(bead_id):
    """Reads a specific bead by searching across all potential directories."""
    for directory in get_dirs():
        file_path = directory / f"{bead_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
    raise FileNotFoundError(f"Bead {bead_id} not found in any directory.")

def update_bead(bead_id, updates):
    """Updates an existing bead in whichever directory it was found."""
    for directory in get_dirs():
        file_path = directory / f"{bead_id}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                bead_data = json.load(f)
            bead_data.update(updates)
            bead_data["updated_at"] = datetime.utcnow().isoformat()
            with open(file_path, "w") as f:
                json.dump(bead_data, f, indent=4)
            print(f"Updated bead: {bead_id}")
            return bead_data
    raise FileNotFoundError(f"Bead {bead_id} not found in any directory.")

def list_beads(status=None):
    """Lists all beads across all directories, optionally filtered by status."""
    beads = []
    for directory in get_dirs():
        for file_path in directory.glob("*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                if status is None or data.get("status") == status:
                    beads.append(data)
    return beads

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for b in list_beads():
            print(f"[{b['status'].upper()}] {b['id']}: {b['title']}")
