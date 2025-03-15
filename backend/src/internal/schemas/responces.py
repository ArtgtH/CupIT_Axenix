from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class TransportType(str, Enum):
    bus = "bus"
    train = "train"
    plane = "plane"
    ship = "ship"
    walk = "walk"


class ResponseType(str, Enum):
    message = "message"
    schedule = "schedule"


class MessageResponse(BaseModel):
    type: ResponseType = Field(ResponseType.message, description="Type of response")
    text: str = Field(..., description="Message response")


class ScheduleObject(BaseModel):
    type: TransportType = Field(..., description="Type of transport")
    time_start_utc: int = Field(..., description="Start time in UTC")
    time_end_utc: int = Field(..., description="End time in UTC")
    place_start: str = Field(..., description="Start location")
    place_finish: str = Field(..., description="End location")
    ticket_url: str = Field(..., description="URL for the ticket")


class ScheduleResponse(BaseModel):
    type: ResponseType = Field(ResponseType.schedule, description="Type of response")
    objects: List[ScheduleObject] = Field(..., description="List of schedule objects")
