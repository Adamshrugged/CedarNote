from sqlmodel import SQLModel, Field # type: ignore
from typing import Optional
from datetime import datetime

class FriendRequest(SQLModel, table=True): # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    from_email: str = Field(index=True)
    to_email: str = Field(index=True)
    status: str = Field(default="pending")  # could also be "accepted", "declined"
    created_at: datetime = Field(default_factory=datetime.utcnow)
