#!/bin/bash

# Проверяем, установлен ли Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker перед запуском."
    echo "   Инструкции: https://docs.docker.com/get-docker/"
    exit 1
fi

# Проверяем, установлен ли Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose перед запуском."
    echo "   Инструкции: https://docs.docker.com/compose/install/"
    exit 1
fi

# Проверяем, запущен ли Docker демон
if ! docker info &> /dev/null; then
    echo "❌ Docker демон не запущен. Пожалуйста, запустите Docker перед запуском."
    exit 1
fi

echo "🐳 Запускаем Docker контейнеры..."

# Создаем необходимые директории
mkdir -p uploads results

# Запускаем контейнеры
docker-compose up -d

# Проверяем, запустились ли контейнеры
if [ $? -eq 0 ]; then
    echo "✅ Контейнеры успешно запущены!"
    echo "⏳ При первом запуске может потребоваться некоторое время для загрузки модели llama3.2 (около 4 ГБ)"
    echo "🌐 Откройте веб-браузер и перейдите по адресу: http://localhost:5100"
    
    # Открываем браузер (работает на macOS, Linux и Windows с WSL)
    case "$(uname -s)" in
        Darwin)
            open "http://localhost:5100"
            ;;
        Linux)
            if command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:5100"
            elif command -v gnome-open &> /dev/null; then
                gnome-open "http://localhost:5100"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*)
            start "http://localhost:5100"
            ;;
    esac
else
    echo "❌ Не удалось запустить контейнер. Проверьте логи Docker."
    docker-compose logs
fi