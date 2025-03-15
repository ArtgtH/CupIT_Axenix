from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class TransportType(str, Enum):
    bus = "bus"
    train = "train"
    plane = "plane"
    ship = "ship"
    walk = "walk"


class MessageResponse(BaseModel):
    type: str = Field("message", description="Type of response")
    text: str = Field(..., description="Markdown formatted message")


class ScheduleObject(BaseModel):
    type: TransportType = Field(..., description="Type of transport")
    time_start_utc: int = Field(..., description="Start time in UTC")
    time_end_utc: int = Field(..., description="End time in UTC")
    place_start: str = Field(..., description="Start location")
    place_finish: str = Field(..., description="End location")
    ticket_url: str = Field(..., description="URL for the ticket")


class ScheduleResponse(BaseModel):
    type: str = Field("schedule", description="Type of response")
    objects: List[ScheduleObject] = Field(..., description="List of schedule objects")
