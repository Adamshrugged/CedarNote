from sqlmodel import SQLModel, Field #type: ignore
from typing import Optional
from datetime import datetime

class SharedNote(SQLModel, table=True): #type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_email: str = Field(index=True)
    note_path: str = Field(index=True)  # This is your virtual path
    shared_with_email: str = Field(index=True)
    shared_at: datetime = Field(default_factory=datetime.utcnow)
