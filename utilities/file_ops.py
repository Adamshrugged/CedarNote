import os, json
from pathlib import Path
from core.config import SHARED_FILE


def list_folders(base_dir: Path) -> list[str]:
    folders = [""]
    folders += sorted([
        str(p.relative_to(base_dir))
        for p in base_dir.rglob("*")
        if p.is_dir()
    ])
    return folders


def resolve_safe_path(base_dir: str, user_path: str) -> Path:
    """
    Ensure the final resolved path is inside the user's base directory.
    """
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()

    if not str(target).startswith(str(base)):
        raise ValueError("Invalid path: attempted directory traversal")

    return target


def get_users_shared_with(owner: str, note_path: str) -> list[str]:
    shared = load_shared()
    return shared.get(owner, {}).get(note_path, [])


# Used for sharing files between users
def load_shared():
    if not os.path.exists(SHARED_FILE):
        return {}
    with open(SHARED_FILE, "r") as f:
        return json.load(f)

def save_shared(data):
    with open(SHARED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_notes_shared_with(username: str):
    shared = load_shared()
    result = []
    for owner, notes in shared.items():
        for note, users in notes.items():
            if username in users:
                result.append((owner, note))
    return result
