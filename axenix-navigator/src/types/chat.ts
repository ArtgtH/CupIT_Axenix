export type TransportType = 'bus' | 'train' | 'plane' | 'ship' | 'walk';

export interface ScheduleItem {
  type: TransportType;
  time_start_utc: number;
  time_end_utc: number;
  place_start: string;
  place_finish: string;
  ticket_url: string;
}

export interface MessageResponse {
  type: 'message';
  text: string;
}

export interface ScheduleResponse {
  type: 'schedule';
  objects: ScheduleItem[];
}

export type ApiResponse = MessageResponse | ScheduleResponse;

export interface ChatMessage {
  text: string;
  isBot: boolean;
  schedule?: ScheduleItem[];
} 