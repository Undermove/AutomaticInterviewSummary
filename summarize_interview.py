#!/usr/bin/env python3
# summarize_interview.py
import subprocess
import sys
import os
from pathlib import Path

def transcribe(input_path: str) -> str:
    """Распознавание речи через faster-whisper (поддержка .mp4 напрямую)"""
    from faster_whisper import WhisperModel
    
    # Загружаем модель (используем "base" как и раньше)
    model = WhisperModel("base")
    
    # Выполняем транскрипцию
    segments, info = model.transcribe(input_path)
    
    # Собираем текст из всех сегментов
    result = ""
    for segment in segments:
        result += segment.text + " "
    
    return result.strip()


def summarize_with_ollama(text: str) -> str:
    import os
    import requests
    import json
    
    prompt = f"""
Ты — помощник, делающий краткое и структурированное саммари техсобесов.
Сделай короткий обзор по следующему тексту:
{text}
"""
    try:
        # Получаем хост Ollama из переменной окружения или используем значение по умолчанию
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        
        # Формируем URL для API
        url = f"{ollama_host}/api/generate"
        
        # Отправляем запрос к API Ollama
        response = requests.post(
            url,
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        
        # Проверяем статус ответа
        if response.status_code != 200:
            raise RuntimeError(f"Ошибка API Ollama: {response.text}")
        
        # Получаем результат
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"Ошибка при вызове Ollama: {e}")


def main():
    if len(sys.argv) < 2:
        print("❗ Использование: python summarize_interview.py <video_or_audio_file> [--use-existing-transcript]")
        sys.exit(1)

    input_path = sys.argv[1]
    use_existing = "--use-existing-transcript" in sys.argv
    
    if not Path(input_path).exists():
        print("❗ Указанный файл не существует")
        sys.exit(1)

    transcript_path = Path("transcript.txt")
    
    if use_existing and transcript_path.exists():
        print("📝 Используем существующую транскрипцию...")
        text = transcript_path.read_text()
    else:
        print("🧠 Распознаем речь...")
        text = transcribe(input_path)
        transcript_path.write_text(text)

    print("📚 Создаем саммари...")
    summary = summarize_with_ollama(text)

    summary_path = Path("summary.txt")
    summary_path.write_text(summary)

    print("\n✅ Готово!")
    print(f"\n📝 Расшифровка сохранена в: {transcript_path.resolve()}")
    print(f"📄 Саммари сохранено в: {summary_path.resolve()}")


if __name__ == "__main__":
    main()
