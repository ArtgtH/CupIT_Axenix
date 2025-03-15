from typing import Union

from fastapi import APIRouter

from internal.schema.requests import TaskRequest
from internal.schema.responces import MessageResponse, ScheduleResponse
from internal.service.test import imitate

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/request", response_model=Union[MessageResponse, ScheduleResponse])
async def process_user_request(user_request: TaskRequest):
    text = user_request.text

    if res := imitate(text):
        return res
    else:
        return MessageResponse(text="This is a sample markdown message.")
