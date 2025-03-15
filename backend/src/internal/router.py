import os
from typing import Union, AsyncGenerator

import redis.asyncio as redis
from fastapi import APIRouter, Depends

from internal.schemas.redis import RedisMessage, Role
from internal.schemas.requests import TaskRequest
from internal.schemas.responces import MessageResponse, ScheduleResponse
from internal.service.ai_starter import talk_with_god

REDIS_URL = os.getenv("REDIS_URL")

router = APIRouter(prefix="/api", tags=["api"])


async def get_redis() -> AsyncGenerator:
	print(REDIS_URL)
	redis_client = redis.Redis.from_url(REDIS_URL)
	try:
		yield redis_client
	finally:
		redis_client.close()


@router.post("/request", response_model=Union[MessageResponse, ScheduleResponse])
async def process_user_request(user_request: TaskRequest, redis_client=Depends(get_redis)):
	text = user_request.text
	session_id = str(user_request.id)

	previous_messages_raw = await redis_client.lrange("messages", 0, -1)
	previous_messages = [RedisMessage.parse_raw(msg) for msg in previous_messages_raw]

	message = RedisMessage(role=Role.user, state="Уточняем", text=text)
	await redis_client.rpush(session_id, message.json())

	res = talk_with_god(text, previous_messages)
	if isinstance(res, MessageResponse):
		answer = RedisMessage(role=Role.ai, state="Уточняем", text=res.text)
		await redis_client.rpush(session_id, answer.json())

	return res
