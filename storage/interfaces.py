from abc import ABC, abstractmethod
from typing import List, Optional

class NoteStorage(ABC):
    @abstractmethod
    def list_folder(self, user: str, folder_path: str) -> List[dict]:
        pass

    @abstractmethod
    def get_note(self, user: str, virtual_path: str) -> Optional[dict]:
        pass

    @abstractmethod
    def save_note(self, user: str, virtual_path: str, content: str) -> None:
        pass

    @abstractmethod
    def delete_note(self, user: str, virtual_path: str) -> bool:
        pass

    @abstractmethod
    def create_folder(self, user: str, folder_path: str) -> None:
        pass

    @abstractmethod
    def delete_folder(self, user: str, folder_path: str) -> bool:
        pass
