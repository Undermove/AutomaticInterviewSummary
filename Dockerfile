FROM python:3.10-slim

WORKDIR /app

# Установка необходимых системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY summarize_interview.py .
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Предзагрузка моделей whisper
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

# Создание необходимых директорий
RUN mkdir -p uploads results

# Открытие портов
EXPOSE 5000

# Запуск приложения
CMD ["python", "app.py"]