# Axenix Navigator

## Описание проекта
Axenix Navigator - это инновационное навигационное решение, разработанное в рамках хакатона для компании Axenix. Проект представляет собой интеллектуальную систему навигации, которая помогает пользователям эффективно ориентироваться в пространстве с использованием современных технологий.

## Установка и запуск проекта

### Предварительные требования
- Docker и Docker Compose
- Node.js (для локальной разработки фронтенда)
- Python 3.8+ (для локальной разработки бэкенда)

### Запуск через Docker
1. Клонируйте репозиторий:
```bash
git clone [URL репозитория]
cd CupIT_Axenix
```

2. Запустите проект с помощью Docker Compose:
```bash
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost

### Локальная разработка

#### Бэкенд
1. Перейдите в директорию backend:
```bash
cd backend
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
uvicorn src.main:app --reload
```

#### Фронтенд
1. Перейдите в директорию axenix-navigator:
```bash
cd axenix-navigator
```

2. Установите зависимости:
```bash
npm install
```

3. Запустите приложение:
```bash
npm start
```

## Основной функционал проекта
- Интеллектуальная навигация
- Интеграция с Yandex API
- Кэширование данных через Redis
- Адаптивный пользовательский интерфейс
- Оптимизированная маршрутизация

## Технологии и инструменты

### Фронтенд
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

### Бэкенд
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### Инфраструктура
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

## Архитектура проекта
Проект построен на микросервисной архитектуре и включает следующие компоненты:

- Frontend (React + TypeScript)
- Backend API (FastAPI)
- Redis для кэширования
- Nginx для проксирования и раздачи статики

```
├── axenix-navigator/     # Frontend приложение
├── backend/             # Backend API
├── docs/               # Документация
├── docker-compose.yaml # Конфигурация Docker
└── nginx.conf         # Конфигурация Nginx
```

## Демонстрация работы проекта
[Здесь будут скриншоты приложения]

## Планы по улучшению
- Добавление поддержки офлайн-режима
- Интеграция с дополнительными картографическими сервисами
- Улучшение производительности кэширования
- Расширение функционала аналитики маршрутов

## Лицензия
MIT License

## Команда проекта
- Якимов Роман, МИСИС, FullStack
- Сабанцева Саша, ИТМО, Product Manager
- Игитов Максим, ИТМО, Backend
- Вичук Артем, ИТМО, Backend
- Богодист Сева, ИТМО, NLP specialist
