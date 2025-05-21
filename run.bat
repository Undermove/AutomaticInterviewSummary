@echo off
REM run.bat - Удобный скрипт для запуска summarize_interview.py на Windows

REM Проверка наличия виртуального окружения
if not exist "venv" (
    echo ❌ Виртуальное окружение не найдено. Запустите сначала setup.bat
    exit /b 1
)

REM Активация виртуального окружения
call venv\Scripts\activate.bat

REM Проверка аргументов
if "%~1"=="" (
    echo ❗ Использование: run.bat путь\к\файлу.mp4 [--use-existing-transcript]
    echo    Пример: run.bat test.mp4
    echo    Пример с использованием существующей транскрипции: run.bat test.mp4 --use-existing-transcript
    exit /b 1
)

REM Запуск скрипта с переданными аргументами
python summarize_interview.py %*

REM Деактивация виртуального окружения
deactivate