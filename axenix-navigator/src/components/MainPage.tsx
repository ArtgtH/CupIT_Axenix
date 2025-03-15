import React from 'react';
import { useNavigate } from 'react-router-dom';

const MainPage: React.FC = () => {
  const navigate = useNavigate();

  const handleStartClick = () => {
    // Добавляем плавное исчезновение перед переходом
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease-in-out';
    
    setTimeout(() => {
      navigate('/chat');
      // Возвращаем opacity после перехода
      requestAnimationFrame(() => {
        document.body.style.opacity = '1';
      });
    }, 300);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-border px-4 sm:px-10 py-3">
        <div className="flex items-center gap-2 text-secondary">
          <img src="/images/logo-big.png" alt="Axenix" className="h-6 w-auto" />
          <h2 className="text-lg font-bold leading-tight tracking-[-0.015em]">Навигатор Axenix</h2>
        </div>
      </header>
      <main className="flex-1 px-4 md:px-40 py-5">
        <div className="max-w-[960px] mx-auto">
          <div className="mb-8">
            <div className="p-0 sm:p-4">
              <div
                className="flex min-h-[480px] flex-col gap-6 bg-cover bg-center bg-no-repeat sm:gap-8 sm:rounded-xl items-center justify-center p-4"
                style={{backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%), url("https://cdn.usegalileo.ai/sdxl10/120f3b41-f384-4160-98c0-786dd6604580.png")'}}
              >
                <div className="flex flex-col gap-2 text-center">
                  <h1 className="text-white text-3xl sm:text-4xl md:text-5xl font-black leading-tight tracking-[-0.033em]">
                    Навигатор Axenix
                  </h1>
                  <h2 className="text-white text-sm sm:text-base font-normal leading-normal">
                    Ваш личный путеводитель по миру
                  </h2>
                </div>
                <button
                  onClick={handleStartClick}
                  className="flex min-w-[84px] max-w-[480px] items-center justify-center overflow-hidden rounded-xl h-10 sm:h-12 px-4 sm:px-5 bg-primary text-white text-sm sm:text-base font-bold leading-normal tracking-[0.015em] hover:bg-opacity-90 transition-all"
                >
                  <span className="truncate">Начать</span>
                </button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 px-4 py-3">
            <div className="flex flex-col gap-2 rounded-lg border border-[#e6dedb] p-3">
              <p className="text-secondary text-2xl font-bold leading-tight">AI</p>
              <p className="text-tertiary text-sm">Умный поиск билетов</p>
            </div>
            <div className="flex flex-col gap-2 rounded-lg border border-[#e6dedb] p-3">
              <p className="text-secondary text-2xl font-bold leading-tight">1000+</p>
              <p className="text-tertiary text-sm">Городов в базе</p>
            </div>
            <div className="flex flex-col gap-2 rounded-lg border border-[#e6dedb] p-3">
              <p className="text-secondary text-2xl font-bold leading-tight">100+</p>
              <p className="text-tertiary text-sm">Авиакомпаний в поиске</p>
            </div>
          </div>

          <h2 className="text-secondary text-xl sm:text-2xl font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-8">
            Популярные направления
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 p-4">
            {[
              { name: 'Токио', image: 'https://cdn.usegalileo.ai/sdxl10/149035e5-669b-47ab-a775-2d9d150694ab.png' },
              { name: 'Париж', image: 'https://cdn.usegalileo.ai/sdxl10/a99889f3-d14f-4763-93bf-239704345bec.png' },
              { name: 'Нью-Йорк', image: 'https://cdn.usegalileo.ai/sdxl10/a55a1e89-77bd-4975-bcca-9755528ce8c5.png' },
              { name: 'Лондон', image: 'https://cdn.usegalileo.ai/sdxl10/1c2cd53b-52b9-4e40-9bfa-7c85151bab26.png' },
              { name: 'Дубай', image: 'https://cdn.usegalileo.ai/sdxl10/2cce83e7-b63e-4de7-b50c-457642640971.png' }
            ].map((city, index) => (
              <div key={index} className="overflow-hidden">
                <div
                  className="w-full bg-center bg-no-repeat aspect-video bg-cover rounded-xl transition-all duration-300 ease-in-out hover:brightness-110 hover:saturate-150"
                  style={{backgroundImage: `url("${city.image}")`}}
                ></div>
                <p className="text-secondary text-base font-medium mt-2">{city.name}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default MainPage; 