from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    ai = "ai"
    user = "user"


class RedisMessage(BaseModel):
    role: Role = Field(..., description="Role of sender")
    state: str = Field(..., description="State of thread")
    text: str = Field(..., description="Message text")
