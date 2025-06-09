import os 

# Shows all sub folders
def build_folder_tree(base_path):
    folder_tree = []

    for root, dirs, files in os.walk(base_path):
        # Show relative path from NOTES_DIR
        relative_root = os.path.relpath(root, base_path)
        if relative_root == ".":
            relative_root = ""  # Root folder

        folder_info = {
            "folder": relative_root,
            "notes": [],
        }

        for file in files:
            if file.endswith(".md"):
                folder_info["notes"].append(file)

        if folder_info["notes"] or relative_root:
            folder_tree.append(folder_info)

    return folder_tree