from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    ai = "ai"
    user = "user"


class RedisMessage(BaseModel):
    role: Role = Field(..., description="Role of sender")
    text: str = Field(..., description="Message text")


class ThreadStatus(BaseModel):
    date: str = Field(..., description="Date")
    start_city: str = Field(..., description="Start city")
    end_city: str = Field(..., description="End city")
    mid_city: str = Field(..., description="Mid city")
