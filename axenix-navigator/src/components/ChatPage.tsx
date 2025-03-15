import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Message {
  text: string;
  isBot: boolean;
}

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    { text: 'Откуда вы отправляетесь?', isBot: true }
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
  const mockApiCall = async (message: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const responses = [
      'Отличный выбор! Куда бы вы хотели отправиться?',
      'Какие даты поездки вы рассматриваете?',
      'Какой бюджет на поездку вы планируете?',
      'Предпочитаете активный отдых или спокойное времяпрепровождение?'
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
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
      const botMessage = { text: response, isBot: true };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error getting response:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-border px-4 sm:px-10 py-3">
        <div className="flex items-center gap-4 text-secondary">
          <div 
            className="w-4 h-4 cursor-pointer hover:opacity-80 transition-opacity" 
            onClick={handleNavigateHome}
          >
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" clipRule="evenodd" d="M24 4H42V17.3333V30.6667H24V44H6V30.6667V17.3333H24V4Z" fill="currentColor"></path>
            </svg>
          </div>
          <h2 className="text-lg font-bold leading-tight tracking-[-0.015em]">Навигатор Axenix</h2>
        </div>
      </header>
      <main className="flex-1 px-4 md:px-40 py-5 flex justify-center">
        <div className="w-full max-w-2xl flex flex-col">
          <div className="flex flex-wrap justify-between gap-3 p-4">
            <h1 className="text-secondary text-3xl sm:text-4xl font-black leading-tight tracking-[-0.033em]">
              Навигатор Axenix
            </h1>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-4">
            {messages.map((message, index) => (
              <div key={index} className={`flex items-end gap-3 p-4 ${!message.isBot ? 'flex-row-reverse' : ''}`}>
                {message.isBot && (
                  <div
                    className="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-10 shrink-0"
                    style={{backgroundImage: 'url("https://cdn.usegalileo.ai/sdxl10/0830ed68-1304-4318-a721-169d01873e24.png")'}}
                  />
                )}
                <div className={`flex flex-col gap-1 ${message.isBot ? 'items-start' : 'items-end'} max-w-[80%]`}>
                  {message.isBot && (
                    <p className="text-tertiary text-xs">Навигатор Axenix</p>
                  )}
                  <div className={`rounded-xl px-4 py-3 ${
                    message.isBot ? 'bg-[#f5f1f0] text-secondary' : 'bg-primary text-white'
                  }`}>
                    <p className="text-base break-words">{message.text}</p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="sticky bottom-0 bg-white px-4 py-3">
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