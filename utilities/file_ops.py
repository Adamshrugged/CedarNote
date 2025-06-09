import os

def list_folders(base_path):
    folders = []
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            rel_path = os.path.relpath(os.path.join(root, d), base_path)
            folders.append(rel_path)
    return sorted(folders)