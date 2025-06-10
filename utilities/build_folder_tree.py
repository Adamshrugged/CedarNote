import os
import pathlib
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

def build_folder_tree(notes_dir: str):
    tree = []
    for folder_path, _, files in os.walk(notes_dir):
        folder = os.path.relpath(folder_path, notes_dir)
        folder_data = {"folder": None if folder == '.' else folder, "notes": []}

        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(folder_path, file)
                title = extract_title_from_markdown(full_path) or file
                relative_path = os.path.relpath(full_path, notes_dir)

                folder_data["notes"].append({
                    "filename": relative_path,
                    "title": title
                })

        if folder_data["notes"]:
            tree.append(folder_data)
    return tree
