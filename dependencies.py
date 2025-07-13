from storage.filesystem import FileSystemStorage
from storage.interfaces import NoteStorage

def get_storage() -> NoteStorage:
    return FileSystemStorage()
