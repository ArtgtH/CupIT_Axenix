from internal.schema.responces import ScheduleResponse, ScheduleObject, TransportType


def imitate(input_text: str) -> ScheduleResponse:
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

    res = ScheduleResponse(type="schedule", objects=[obj_1, obj_2])

    return res
