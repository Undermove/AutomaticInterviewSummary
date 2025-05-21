#!/usr/bin/env python3
import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import threading
import time
from summarize_interview import transcribe, summarize_with_ollama

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB максимальный размер файла
app.config['RESULTS_FOLDER'] = 'results'

# Создаем необходимые директории
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Словарь для хранения статуса обработки
processing_status = {}

@app.route('/')
def index():
    return render_template('index.html')

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