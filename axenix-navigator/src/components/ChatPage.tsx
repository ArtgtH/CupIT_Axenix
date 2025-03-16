import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatMessage, ApiResponse } from '../types/chat';

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { text: 'Я — Саша, ваш умный помощник в планировании поездки. \n\nПожалуйста, напишите мне, откуда, куда и когда вы планируете отправиться, даже можете указать сложный маршрут из нескольких городов, и я смогу вам помочь с выбором транспорта, маршрута и покупкой билетов!\n\nУчти, что ты можешь выбрать свои приоритеты из 3-х видов транспорта: автобуса, самолета и поезда', isBot: true }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleNavigateHome = () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease-in-out';
    
    setTimeout(() => {
      navigate('/');
      requestAnimationFrame(() => {
        document.body.style.opacity = '1';
      });
    }, 300);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Мок функции для работы с бэкендом
  const mockApiCall = async (message: string): Promise<ApiResponse> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Пример ответа с расписанием
    if (message.toLowerCase().includes('санкт-петербург') && message.toLowerCase().includes('москва')) {
      return {
        type: 'schedule',
        objects: [
          {
            type: 'train',
            time_start_utc: Math.floor(Date.now() / 1000) + 86400, // завтра
            time_end_utc: Math.floor(Date.now() / 1000) + 86400 + 7200, // +2 часа
            place_start: 'Санкт-Петербург',
            place_finish: 'Тверь',
            ticket_url: 'https://example.com/ticket1'
          },
          {
            type: 'bus',
            time_start_utc: Math.floor(Date.now() / 1000) + 86400 + 7200 + 1800, // +30 минут после поезда
            time_end_utc: Math.floor(Date.now() / 1000) + 86400 + 7200 + 1800 + 3600, // +1 час
            place_start: 'Тверь',
            place_finish: 'Москва',
            ticket_url: 'https://example.com/ticket2'
          }
        ]
      };
    }
    
    // Пример ответа с расписанием для других городов
    if (message.toLowerCase().includes('москва') && message.toLowerCase().includes('сочи')) {
      return {
        type: 'schedule',
        objects: [
          {
            type: 'plane',
            time_start_utc: Math.floor(Date.now() / 1000) + 86400,
            time_end_utc: Math.floor(Date.now() / 1000) + 86400 + 7200,
            place_start: 'Москва',
            place_finish: 'Ростов-на-Дону',
            ticket_url: 'https://example.com/ticket3'
          },
          {
            type: 'bus',
            time_start_utc: Math.floor(Date.now() / 1000) + 86400 + 7200 + 3600,
            time_end_utc: Math.floor(Date.now() / 1000) + 86400 + 7200 + 3600 + 7200,
            place_start: 'Ростов-на-Дону',
            place_finish: 'Сочи',
            ticket_url: 'https://example.com/ticket4'
          }
        ]
      };
    }
    
    // Пример текстового ответа
    const responses = [
      'Отличный выбор! Куда бы вы хотели отправиться?',
      'Какие даты поездки вы рассматриваете?',
      'Какой бюджет на поездку вы планируете?',
      'Предпочитаете активный отдых или спокойное времяпрепровождение?'
    ];
    
    return {
      type: 'message',
      text: responses[Math.floor(Math.random() * responses.length)]
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = { text: inputValue, isBot: false };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await mockApiCall(inputValue);
      if (response.type === 'message') {
        setMessages(prev => [...prev, { text: response.text, isBot: true }]);
      } else if (response.type === 'schedule') {
        setMessages(prev => [...prev, { 
          text: 'Вот подходящие варианты маршрута:', 
          isBot: true,
          schedule: response.objects 
        }]);
      }
    } catch (error) {
      console.error('Error getting response:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransportIcon = (type: string) => {
    switch (type) {
      case 'plane': return '✈️';
      case 'train': return '🚂';
      case 'bus': return '🚌';
      case 'ship': return '🚢';
      case 'walk': return '🚶';
      default: return '🚀';
    }
  };

  const translateTransportType = (type: string): string => {
    switch (type) {
      case 'plane': return 'самолет';
      case 'train': return 'поезд';
      case 'bus': return 'автобус';
      case 'ship': return 'корабль';
      case 'walk': return 'пешком';
      default: return type;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-border px-4 sm:px-10 py-3">
        <div className="flex items-center gap-2 text-secondary">
          <img 
            src="/images/logo-big.png" 
            alt="Axenix" 
            className="h-6 w-auto cursor-pointer hover:opacity-80 transition-opacity" 
            onClick={handleNavigateHome}
          />
          <h2 className="text-lg font-bold leading-tight tracking-[-0.015em]">Навигатор Axenix</h2>
        </div>
      </header>
      <main className="flex-1 px-4 md:px-40 py-5 flex justify-center">
        <div className="w-full max-w-2xl flex flex-col h-[calc(100vh-8rem)]">
          <div className="flex-1 overflow-y-auto space-y-4 scroll-smooth pb-4">
            {messages.map((message, index) => (
              <div key={index} className={`flex items-end gap-3 p-4 ${!message.isBot ? 'flex-row-reverse' : ''}`}>
                {message.isBot && (
                  <div
                    className="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-10 shrink-0"
                    style={{backgroundImage: 'url("/images/logo-small.jpg")'}}
                  />
                )}
                <div className={`flex flex-col gap-1 ${message.isBot ? 'items-start' : 'items-end'} max-w-[80%]`}>
                  {message.isBot && (
                    <p className="text-tertiary text-xs">Навигатор Axenix</p>
                  )}
                  <div className={`rounded-xl px-4 py-3 ${
                    message.isBot ? 'bg-[#f5f1f0] text-secondary' : 'bg-primary text-white'
                  }`}>
                    <p className="text-base break-words whitespace-pre-wrap">{message.text}</p>
                  </div>
                  {message.schedule && (
                    <div className="w-full space-y-2 mt-2">
                      {message.schedule.map((item, idx) => (
                        <div key={idx} className="bg-white rounded-xl p-4 border border-[#e6dedb]">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-2xl">{getTransportIcon(item.type)}</span>
                            <span className="text-secondary font-medium capitalize">{translateTransportType(item.type)}</span>
                          </div>
                          <div className="flex justify-between items-center text-sm">
                            <div className="flex flex-col">
                              <span className="text-secondary font-medium">{item.place_start}</span>
                              <span className="text-tertiary">{formatTime(item.time_start_utc)}</span>
                            </div>
                            <div className="h-px flex-1 bg-[#e6dedb] mx-4"></div>
                            <div className="flex flex-col items-end">
                              <span className="text-secondary font-medium">{item.place_finish}</span>
                              <span className="text-tertiary">{formatTime(item.time_end_utc)}</span>
                            </div>
                          </div>
                          <a 
                            href={item.ticket_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="mt-3 block text-center py-2 px-4 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-all"
                          >
                            Купить билет
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="sticky bottom-0 bg-white px-4 py-3 border-t border-border mt-auto">
            <div className="flex items-center gap-3">
              <div className="flex-1 relative">
                <input
                  placeholder="Из Санкт-Петербурга"
                  className="w-full h-12 px-4 rounded-xl bg-[#f5f1f0] text-secondary placeholder-tertiary focus:outline-none"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className={`min-w-[100px] h-12 px-6 rounded-xl bg-primary text-white font-medium transition-all
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}`}
              >
                {isLoading ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default ChatPage;