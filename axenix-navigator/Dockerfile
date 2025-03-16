FROM node:18-alpine as builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Используем легковесный образ для хранения собранных файлов
FROM alpine:3.18

WORKDIR /app

# Копируем собранные файлы из предыдущего этапа
COPY --from=builder /app/build /app/build

# Просто храним файлы, не запускаем сервер
CMD ["sh", "-c", "echo 'Frontend build is ready at /app/build' && sleep infinity"]
