from sqlmodel import SQLModel, Field # type: ignore
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True): # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str]
    picture: Optional[str]
    role: str = Field(default="user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
