@echo off
REM setup.bat - Скрипт для установки всех необходимых компонентов для запуска summarize_interview.py на Windows

echo 🚀 Начинаем установку необходимых компонентов...

REM Проверка наличия Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python не установлен. Пожалуйста, установите Python и запустите скрипт снова.
    echo Скачать Python можно с https://www.python.org/downloads/
    exit /b 1
)

REM Вывод версии Python
python -c "import sys; print(f'📌 Обнаружена версия Python: {sys.version_info.major}.{sys.version_info.minor}')"

REM Создание виртуального окружения
echo 🔧 Создаем виртуальное окружение...
python -m venv venv
call venv\Scripts\activate.bat

REM Установка зависимостей
echo 📦 Устанавливаем необходимые библиотеки...
python -m pip install --upgrade pip
python -m pip install faster-whisper

REM Проверка наличия Ollama
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Ollama не установлена. Для полной функциональности необходимо установить Ollama.
    echo 📝 Скачайте установщик с https://ollama.com/download
) else (
    echo ✅ Ollama уже установлена.
    
    REM Проверка наличия модели llama3
    ollama list | findstr "llama3" >nul
    if %ERRORLEVEL% NEQ 0 (
        echo 🤖 Загружаем модель llama3...
        ollama pull llama3
    ) else (
        echo ✅ Модель llama3 уже установлена.
    )
)

echo 🔍 Проверяем наличие тестового файла...
if not exist "test.mp4" (
    echo ⚠️ Тестовый файл test.mp4 не найден. Для тестирования скрипта необходимо добавить аудио или видео файл.
    echo    Переименуйте ваш файл в test.mp4 или укажите другой файл при запуске скрипта.
)

echo.
echo ✅ Установка завершена! Теперь вы можете запустить скрипт:
echo.
echo    REM Активация виртуального окружения (если оно еще не активировано)
echo    call venv\Scripts\activate.bat
echo.
echo    REM Запуск скрипта с распознаванием речи
echo    python summarize_interview.py путь\к\файлу.mp4
echo.
echo    REM Или использование существующей транскрипции (если файл transcript.txt уже существует)
echo    python summarize_interview.py путь\к\файлу.mp4 --use-existing-transcript
echo.

pause