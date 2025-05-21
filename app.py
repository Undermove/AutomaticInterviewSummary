#!/usr/bin/env python3
import os
import uuid
import requests
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import threading
from summarize_interview import transcribe, summarize_with_ollama

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB максимальный размер файла
app.config['RESULTS_FOLDER'] = 'results'

# Создаем необходимые директории
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Инициализация Ollama - загрузка модели при запуске
def init_ollama():
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    print(f"🤖 Инициализация Ollama на {ollama_host}...")
    
    # Ждем, пока Ollama будет доступна
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{ollama_host}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama доступна")
                break
        except Exception:
            pass
        
        print(f"⏳ Ожидание Ollama... ({i+1}/{max_retries})")
        time.sleep(5)
    
    # Проверяем наличие модели llama3.2
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        models = response.json().get("models", [])
        model_exists = any(model.get("name") == "llama3.2" for model in models)
        
        if not model_exists:
            print("📥 Загрузка модели llama3.2...")
            response = requests.post(
                f"{ollama_host}/api/pull",
                json={"name": "llama3.2"},
            )
            print("✅ Модель llama3.2 загружена")
    except Exception as e:
        print(f"⚠️ Ошибка при инициализации Ollama: {e}")

# Запускаем инициализацию в отдельном потоке
threading.Thread(target=init_ollama, daemon=True).start()

# Словарь для хранения статуса обработки
processing_status = {}

@app.route('/')
def index():
    # Получаем список всех обработанных файлов
    history = get_processing_history()
    return render_template('index.html', history=history)

def get_processing_history():
    """Получает историю всех обработанных файлов"""
    history = []
    
    # Ищем все файлы summary_*.txt в папке results
    summary_files = [f for f in os.listdir(app.config['RESULTS_FOLDER']) 
                    if f.endswith('_summary.txt') and os.path.isfile(os.path.join(app.config['RESULTS_FOLDER'], f))]
    
    for summary_file in summary_files:
        # Извлекаем task_id из имени файла
        task_id = summary_file.replace('_summary.txt', '')
        
        # Проверяем наличие соответствующего файла транскрипции
        transcript_file = f"{task_id}_transcript.txt"
        transcript_path = os.path.join(app.config['RESULTS_FOLDER'], transcript_file)
        
        if os.path.exists(transcript_path):
            # Получаем время создания файла
            timestamp = os.path.getmtime(os.path.join(app.config['RESULTS_FOLDER'], summary_file))
            date_created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            
            # Читаем первые 200 символов саммари для предпросмотра
            with open(os.path.join(app.config['RESULTS_FOLDER'], summary_file), 'r', encoding='utf-8') as f:
                summary_preview = f.read(200)
                if len(summary_preview) == 200:
                    summary_preview += '...'
            
            # Добавляем информацию в историю
            history.append({
                'task_id': task_id,
                'date': date_created,
                'summary_preview': summary_preview
            })
    
    # Сортируем по времени создания (новые сверху)
    history.sort(key=lambda x: x['date'], reverse=True)
    
    return history

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if file:
        # Создаем уникальный ID для задачи
        task_id = str(uuid.uuid4())
        
        # Сохраняем файл с безопасным именем
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
        file.save(file_path)
        
        # Инициализируем статус задачи
        processing_status[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Начало обработки файла...'
        }
        
        # Запускаем обработку в отдельном потоке
        threading.Thread(target=process_file, args=(file_path, task_id)).start()
        
        return jsonify({'task_id': task_id})

def process_file(file_path, task_id):
    try:
        # Обновляем статус - начало транскрипции
        processing_status[task_id] = {
            'status': 'processing',
            'progress': 10,
            'message': 'Распознаем речь...'
        }
        
        # Выполняем транскрипцию
        transcript = transcribe(file_path)
        
        # Сохраняем транскрипцию
        transcript_path = os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_transcript.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # Обновляем статус - начало создания саммари
        processing_status[task_id] = {
            'status': 'processing',
            'progress': 50,
            'message': 'Создаем саммари...'
        }
        
        # Создаем саммари
        summary = summarize_with_ollama(transcript)
        
        # Сохраняем саммари
        summary_path = os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # Обновляем статус - завершено
        processing_status[task_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Обработка завершена',
            'transcript': transcript,
            'summary': summary
        }
        
        # Удаляем исходный файл для экономии места
        os.remove(file_path)
        
    except Exception as e:
        # В случае ошибки обновляем статус
        processing_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Ошибка: {str(e)}'
        }

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in processing_status:
        return jsonify({'error': 'Задача не найдена'}), 404
    
    return jsonify(processing_status[task_id])

@app.route('/download/<task_id>/<file_type>', methods=['GET'])
def download_file(task_id, file_type):
    if file_type not in ['transcript', 'summary']:
        return jsonify({'error': 'Неверный тип файла'}), 400
    
    filename = f"{task_id}_{file_type}.txt"
    return send_from_directory(app.config['RESULTS_FOLDER'], filename, as_attachment=True)

@app.route('/view/<task_id>', methods=['GET'])
def view_result(task_id):
    """Просмотр результатов обработки по task_id"""
    # Проверяем наличие файлов
    summary_path = os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_summary.txt")
    transcript_path = os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_transcript.txt")
    
    if not os.path.exists(summary_path) or not os.path.exists(transcript_path):
        return jsonify({'error': 'Результаты не найдены'}), 404
    
    # Читаем содержимое файлов
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = f.read()
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Возвращаем результаты
    return jsonify({
        'summary': summary,
        'transcript': transcript
    })

# Очистка старых результатов (запускается в отдельном потоке)
def cleanup_old_files():
    while True:
        time.sleep(3600)  # Проверка раз в час
        current_time = time.time()
        
        # Удаляем файлы старше 24 часов
        for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > 86400:
                    os.remove(file_path)
        
        # Очищаем старые записи в словаре статусов
        task_ids = list(processing_status.keys())
        for task_id in task_ids:
            result_files = [
                os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_transcript.txt"),
                os.path.join(app.config['RESULTS_FOLDER'], f"{task_id}_summary.txt")
            ]
            if all(not os.path.exists(f) for f in result_files):
                processing_status.pop(task_id, None)

if __name__ == '__main__':
    # Запускаем поток очистки
    threading.Thread(target=cleanup_old_files, daemon=True).start()
    
    # Запускаем приложение
    app.run(host='0.0.0.0', port=5000)