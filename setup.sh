#!/bin/bash
# setup.sh - Скрипт для установки всех необходимых компонентов для запуска summarize_interview.py

set -e  # Остановка скрипта при любой ошибке

echo "🚀 Начинаем установку необходимых компонентов..."

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен. Пожалуйста, установите Python 3 и запустите скрипт снова."
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "📌 Обнаружена версия Python: $PYTHON_VERSION"

# Создание виртуального окружения
echo "🔧 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo "📦 Устанавливаем необходимые библиотеки..."
pip install --upgrade pip
pip install faster-whisper

# Проверка наличия Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama не установлена. Для полной функциональности необходимо установить Ollama."
    echo "📝 Инструкции по установке Ollama: https://github.com/ollama/ollama"
    
    # Определение операционной системы
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🍎 Обнаружена macOS. Вы можете установить Ollama с помощью Homebrew:"
        echo "   brew install ollama"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "🐧 Обнаружен Linux. Вы можете установить Ollama с помощью:"
        echo "   curl -fsSL https://ollama.com/install.sh | sh"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "🪟 Обнаружена Windows. Скачайте установщик с https://ollama.com/download"
    fi
else
    echo "✅ Ollama уже установлена."
    
    # Проверка наличия модели llama3
    if ! ollama list | grep -q "llama3"; then
        echo "🤖 Загружаем модель llama3..."
        ollama pull llama3
    else
        echo "✅ Модель llama3 уже установлена."
    fi
fi

echo "🔍 Проверяем наличие тестового файла..."
if [ ! -f "test.mp4" ]; then
    echo "⚠️ Тестовый файл test.mp4 не найден. Для тестирования скрипта необходимо добавить аудио или видео файл."
    echo "   Переименуйте ваш файл в test.mp4 или укажите другой файл при запуске скрипта."
fi

echo "
✅ Установка завершена! Теперь вы можете запустить скрипт:

   # Активация виртуального окружения (если оно еще не активировано)
   source venv/bin/activate

   # Запуск скрипта с распознаванием речи
   python3 summarize_interview.py <путь_к_аудио_или_видео_файлу>

   # Или использование существующей транскрипции (если файл transcript.txt уже существует)
   python3 summarize_interview.py <путь_к_аудио_или_видео_файлу> --use-existing-transcript
"