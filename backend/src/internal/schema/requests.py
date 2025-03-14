from uuid import UUID

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    id: UUID = Field(..., description="UUID of the user")
    text: str = Field(..., description="Request text from the user")
