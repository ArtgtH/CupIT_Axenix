import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatMessage, ApiResponse } from '../types/chat';
// @ts-ignore
import { v4 as uuidv4 } from 'uuid';

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { text: 'Я — Саша, ваш умный помощник в планировании поездки. \n\nПожалуйста, напишите мне, откуда, куда и когда вы планируете отправиться, даже можете указать сложный маршрут из нескольких городов, и я смогу вам помочь с выбором транспорта, маршрута и покупкой билетов!\n\nУчти, что ты можешь выбрать свои приоритеты из 3-х видов транспорта: автобуса, самолета и поезда', isBot: true }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [userId] = useState<string>(() => {
    // Пытаемся получить существующий userId из localStorage
    const savedUserId = localStorage.getItem('axenix_user_id');
    if (savedUserId) {
      return savedUserId;
    }
    
    // Если нет, создаем новый и сохраняем
    const newUserId = uuidv4();
    localStorage.setItem('axenix_user_id', newUserId);
    return newUserId;
  });

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

  // Функция для работы с API
  const callApi = async (message: string): Promise<ApiResponse> => {
    try {
      const response = await fetch('https://axenix.space/api/request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: userId,
          text: message
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      return data as ApiResponse;
    } catch (error) {
      console.error('API call failed:', error);
      
      // В случае ошибки возвращаем сообщение об ошибке
      return {
        type: 'message',
        text: 'Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.'
      };
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = { text: inputValue, isBot: false };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await callApi(inputValue);
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
      setMessages(prev => [...prev, { 
        text: 'Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.', 
        isBot: true 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    let dateStr = '';
    if (date.toDateString() === today.toDateString()) {
      dateStr = 'Сегодня';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      dateStr = 'Завтра';
    } else {
      dateStr = date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long'
      });
    }

    const timeStr = date.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });

    return `${dateStr}, ${timeStr}`;
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
    <div className="min-h-screen flex flex-col h-screen">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-border px-3 sm:px-6 md:px-10 py-2 md:py-3 sticky top-0 z-10 bg-white">
        <div className="flex items-center gap-2 text-secondary">
          <img 
            src="/images/logo-big.png" 
            alt="Axenix" 
            className="h-5 sm:h-6 w-auto cursor-pointer hover:opacity-80 transition-opacity" 
            onClick={handleNavigateHome}
          />
          <h2 className="text-base sm:text-lg font-bold leading-tight tracking-[-0.015em]">Навигатор Axenix</h2>
        </div>
      </header>
      <main className="flex-1 px-2 sm:px-4 md:px-10 lg:px-40 py-3 md:py-5 flex justify-center flex-grow">
        <div className="w-full max-w-2xl flex flex-col flex-grow">
          <div className={`flex-grow flex flex-col ${messages.length > 3 ? 'overflow-y-auto' : 'overflow-y-hidden'} pb-3 md:pb-4`}>
            <div className="space-y-3 md:space-y-4 scroll-smooth flex-grow">
              {messages.map((message, index) => (
                <div key={index} className={`flex items-end gap-2 sm:gap-3 p-2 sm:p-3 md:p-4 ${!message.isBot ? 'flex-row-reverse' : ''}`}>
                  {message.isBot && (
                    <div
                      className="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-8 sm:w-10 shrink-0"
                      style={{backgroundImage: 'url("/images/logo-small.jpg")'}}
                    />
                  )}
                  <div className={`flex flex-col gap-1 ${message.isBot ? 'items-start' : 'items-end'} max-w-[85%] sm:max-w-[80%]`}>
                    {message.isBot && (
                      <p className="text-tertiary text-xs">Навигатор Axenix</p>
                    )}
                    <div className={`rounded-xl px-3 py-2 sm:px-4 sm:py-3 ${
                      message.isBot ? 'bg-[#f5f1f0] text-secondary' : 'bg-primary text-white'
                    }`}>
                      <p className="text-sm sm:text-base break-words whitespace-pre-wrap">{message.text}</p>
                    </div>
                    {message.schedule && (
                      <div className="w-full space-y-2 mt-2">
                        {message.schedule.map((item, idx) => (
                          <div key={idx} className="bg-white rounded-xl p-3 sm:p-4 border border-[#e6dedb]">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xl sm:text-2xl">{getTransportIcon(item.type)}</span>
                              <span className="text-secondary text-sm sm:text-base font-medium capitalize">{translateTransportType(item.type)}</span>
                            </div>
                            <div className="flex justify-between items-center text-xs sm:text-sm">
                              <div className="flex flex-col">
                                <span className="text-secondary font-medium">{item.place_start}</span>
                                <span className="text-tertiary">{formatTime(item.time_start_utc)}</span>
                              </div>
                              <div className="h-px flex-1 bg-[#e6dedb] mx-2 sm:mx-4"></div>
                              <div className="flex flex-col items-end">
                                <span className="text-secondary font-medium">{item.place_finish}</span>
                                <span className="text-tertiary">{formatTime(item.time_end_utc)}</span>
                              </div>
                            </div>
                            <a 
                              href={item.ticket_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="mt-2 sm:mt-3 block text-center py-1.5 sm:py-2 px-3 sm:px-4 text-sm bg-primary text-white rounded-lg hover:bg-opacity-90 transition-all"
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
          </div>

          <form onSubmit={handleSubmit} className="sticky bottom-0 bg-white px-2 sm:px-4 py-2 sm:py-3 border-t border-border mt-auto">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex-1 relative">
                <input
                  placeholder="Из Санкт-Петербурга"
                  className="w-full h-10 sm:h-12 px-3 sm:px-4 rounded-xl bg-[#f5f1f0] text-secondary placeholder-tertiary focus:outline-none text-sm sm:text-base"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className={`min-w-[80px] sm:min-w-[100px] h-10 sm:h-12 px-3 sm:px-6 rounded-xl bg-primary text-white font-medium transition-all text-sm sm:text-base
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