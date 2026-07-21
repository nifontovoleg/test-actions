# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY main.py .

# Открываем порт
EXPOSE 8000

# Устанавливаем переменные окружения по умолчанию
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
