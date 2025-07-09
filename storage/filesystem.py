import os
from typing import List, Optional
from utilities.formatting import file_parse_frontmatter




class FileSystemStorage:
    def __init__(self, root_dir="notes"):
        self.root_dir = root_dir

    def _user_path(self, user: str, virtual_path: str) -> str:
        return os.path.join(self.root_dir, user, virtual_path)

    def get_note(self, user: str, virtual_path: str) -> Optional[dict]:
        full_path = os.path.join(self.root_dir, user, virtual_path + ".md")
        if not os.path.isfile(full_path):
            return None

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        metadata = {
            "title": "this is a title"
        }

        return {
            "type": "note",
            "path": virtual_path,
            "content": content,
            "metadata": metadata,
        }

    def save_note(self, user: str, virtual_path: str, content: str) -> None:
        full_path = os.path.join(self.root_dir, user, virtual_path + ".md")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def delete_note(self, user: str, virtual_path: str) -> bool:
        full_path = os.path.join(self.root_dir, user, virtual_path + ".md")
        if os.path.isfile(full_path):
            os.remove(full_path)
            return True
        return False


    def list_folder(self, user: str, folder_path: str) -> Optional[List[dict]]:
        base = os.path.join(self.root_dir, user, folder_path)
        if not os.path.isdir(base):
            return None

        entries = []
        for name in os.listdir(base):
            full_path = os.path.join(base, name)
            relative_path = os.path.join(folder_path, name).replace("\\", "/")

            if os.path.isdir(full_path):
                entries.append({
                    "name": name,
                    "type": "folder",
                    "path": relative_path
                })
            elif name.endswith(".md"):
                full_path = os.path.join(base, name)  # Make sure this is the actual full file path

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    metadata = file_parse_frontmatter(content)
                except Exception as e:
                    print(f"Error reading metadata from {full_path}: {e}")
                    metadata = {}

                display_title = metadata.get("title") if isinstance(metadata, dict) and metadata.get("title") else name[:-3]

                entries.append({
                    "name": display_title,
                    "type": "note",
                    "path": relative_path[:-3],  # strip .md
                    "metadata": metadata
                })
        return entries





    def move_note(self, user: str, virtual_path: str, destination_folder: str):
        # Always use ".md" suffix since that's how your notes are saved
        current_path = os.path.join(self.root_dir, user, virtual_path + ".md")
        filename = os.path.basename(virtual_path) + ".md"
        new_path = os.path.join(self.root_dir, user, destination_folder, filename)

        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        os.rename(current_path, new_path)




    def create_folder(self, user: str, folder_path: str) -> None:
        full_path = self._user_path(user, folder_path)
        os.makedirs(full_path, exist_ok=True)

    def delete_folder(self, user: str, folder_path: str) -> bool:
        full_path = os.path.join(self.root_dir, user, folder_path)

        if not os.path.isdir(full_path):
            return False

        contents = os.listdir(full_path)
        if not contents:
            os.rmdir(full_path)
            return True

        # Check if all items are .md files
        only_notes = all(
            os.path.isfile(os.path.join(full_path, f)) and f.endswith(".md")
            for f in contents
        )

        if only_notes:
            parent_dir = os.path.dirname(full_path)
            for note in contents:
                src = os.path.join(full_path, note)
                dst = os.path.join(parent_dir, note)
                # Avoid overwriting
                if not os.path.exists(dst):
                    os.rename(src, dst)
            os.rmdir(full_path)
            return True

        # Contains subfolders or other types of files — do not delete
        return False


    def rename_folder(self, user: str, current_path: str, new_name: str) -> bool:
        src = os.path.join(self.root_dir, user, current_path)
        dst = os.path.join(os.path.dirname(src), new_name)

        if not os.path.exists(src) or not os.path.isdir(src):
            return False

        if os.path.exists(dst):
            return False  # Avoid overwriting

        os.rename(src, dst)
        return True

