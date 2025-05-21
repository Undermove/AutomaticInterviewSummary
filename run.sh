#!/bin/bash
# run.sh - Удобный скрипт для запуска summarize_interview.py

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено. Запустите сначала ./setup.sh"
    exit 1
fi

# Активация виртуального окружения
source venv/bin/activate

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "❗ Использование: ./run.sh <путь_к_аудио_или_видео_файлу> [--use-existing-transcript]"
    echo "   Пример: ./run.sh test.mp4"
    echo "   Пример с использованием существующей транскрипции: ./run.sh test.mp4 --use-existing-transcript"
    exit 1
fi

# Запуск скрипта с переданными аргументами
python3 summarize_interview.py "$@"

# Деактивация виртуального окружения
deactivate