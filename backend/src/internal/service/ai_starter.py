from typing import List

from internal.schemas.redis import RedisMessage
from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType, MessageResponse


def talk_with_god(input_text: str, messages: List[RedisMessage]) -> ScheduleResponse | MessageResponse:
	"""
	Через эту пиздатню я отправляю в LLM запрос
	Как я представляю механзим работы:
	1) LLM все прочитала
	2.1) Если ей хватает информации, чтобы сделать запрос к максу, то она дергает максу
	2.2) Если ей не хватает информации, то генерит сообщение
	3.1) Возвращает распиание
	3.2) Возвращает сообщение с еще одним уточняющим вопросом
	
	:param input_text: текст запроса
	:param messages: контекст из последних сообщений
	:return: расписание(ScheduleResponse) | ответное сообщение(MessageResponse)
	"""
	obj_1 = ScheduleObject(
		type=TransportType.bus,
		time_start_utc=1620000000,
		time_end_utc=1620003600,
		place_start="City A",
		place_finish="City B",
		ticket_url="http://example.com/ticket",
	)

	obj_2 = ScheduleObject(
		type=TransportType.ship,
		time_start_utc=1620000000,
		time_end_utc=1620003600,
		place_start="City A",
		place_finish="City B",
		ticket_url="http://example.com/ticket",
	)

	res_1 = ScheduleResponse(objects=[obj_1, obj_2])

	res_2 = MessageResponse(text="письки письки письки")

	return res_2
