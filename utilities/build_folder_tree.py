import os
from pathlib import Path
import yaml

def extract_title_from_markdown(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if lines[0].strip() != "---":
            return None  # No frontmatter

        yaml_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)

        metadata = yaml.safe_load("".join(yaml_lines))
        return metadata.get("title")
    except Exception:
        return None



def build_folder_tree(base_dir: Path) -> dict:
    tree = {
        "notes": [],
        "children": {}
    }

    for root, dirs, files in os.walk(base_dir):
        rel_root = Path(root).relative_to(base_dir)
        node = tree

        # Traverse into the appropriate nested node
        if rel_root != Path("."):
            for part in rel_root.parts:
                node = node["children"].setdefault(part, {"notes": [], "children": {}})

        # Ensure node keys exist
        node.setdefault("notes", [])
        node.setdefault("children", {})

        for file in files:
            if file.endswith(".md"):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_dir)

                # Use the extracted title if available, fallback to filename stem
                title = extract_title_from_markdown(full_path) or rel_path.stem

                node["notes"].append({
                    "title": title,
                    "filename": str(rel_path)
                })

    return tree

