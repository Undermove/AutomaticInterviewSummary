@echo off
echo 🐳 Запускаем Docker контейнеры...

REM Проверяем, установлен ли Docker
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker не установлен. Пожалуйста, установите Docker перед запуском.
    echo    Инструкции: https://docs.docker.com/get-docker/
    exit /b 1
)

REM Проверяем, установлен ли Docker Compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose перед запуском.
    echo    Инструкции: https://docs.docker.com/compose/install/
    exit /b 1
)

REM Создаем необходимые директории
if not exist uploads mkdir uploads
if not exist results mkdir results

REM Запускаем контейнеры
docker-compose up -d

if %ERRORLEVEL% equ 0 (
    echo ✅ Контейнеры успешно запущены!
    echo ⏳ При первом запуске может потребоваться некоторое время для загрузки модели llama3.2 (около 4 ГБ)
    echo 🌐 Откройте веб-браузер и перейдите по адресу: http://localhost:5100
    
    REM Открываем браузер
    start http://localhost:5100
) else (
    echo ❌ Не удалось запустить контейнер. Проверьте логи Docker.
    docker-compose logs
)

pause