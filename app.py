import os
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dubber import VideoDubber
from clipper import VideoClipper
from watermark import WatermarkRemover

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory job state tracker
jobs = {}

def bg_process(job_id, input_path, filename, mode, source=None, target=None):
    try:
        jobs[job_id]['status'] = 'processing'
        
        if mode == 'dub':
            jobs[job_id]['message'] = 'Transcribiendo y traduciendo audio... Esto puede tomar varios minutos.'
            
            original_name = filename.rsplit('.', 1)[0]
            output_filename = f"{original_name}_{target}.mp4"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            dubber = VideoDubber(source_lang=source, target_lang=target)
            dubber.process_video(input_path, output_path)
            
            jobs[job_id]['status'] = 'done'
            jobs[job_id]['result_file'] = output_filename
            jobs[job_id]['message'] = '¡Proceso finalizado con éxito!'
            
        elif mode == 'clip':
            jobs[job_id]['message'] = 'Generando clips verticales... Por favor espera.'
            
            original_name = filename.rsplit('.', 1)[0]
            output_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"clips_{job_id}")
            clipper = VideoClipper(clip_duration=60, max_clips=None)
            generated_clips = clipper.generate_clips(input_path, output_dir, base_name=f"{original_name}_clip")
            
            jobs[job_id]['status'] = 'done'
            jobs[job_id]['result_folder'] = f"clips_{job_id}"
            jobs[job_id]['clips'] = generated_clips
            jobs[job_id]['message'] = f'¡Se generaron {len(generated_clips)} clips exitosamente!'

        elif mode == 'watermark':
            jobs[job_id]['message'] = 'Buscando y difuminando marca de agua... Esto tomará un momento.'
            original_name = filename.rsplit('.', 1)[0]
            output_filename = f"{original_name}_clean.mp4"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            remover = WatermarkRemover()
            success = remover.process_video(input_path, output_path)
            
            if success:
                jobs[job_id]['status'] = 'done'
                jobs[job_id]['result_file'] = output_filename
                jobs[job_id]['message'] = '¡Marca de agua procesada con éxito!'
            else:
                jobs[job_id]['status'] = 'error'
                jobs[job_id]['message'] = 'Hubo un problema al procesar el video.'

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    file = request.files['video']
    
    direction = request.form.get('direction', 'en-es')
    mode = request.form.get('mode', 'dub') # 'dub', 'clip' or 'watermark'
    
    source = 'en'
    target = 'es'
    if direction == 'es-en':
        source = 'es'
        target = 'en'
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
        
    filename = secure_filename(file.filename)
    job_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{job_id}_{filename}")
    
    file.save(input_path)
    
    jobs[job_id] = {'status': 'queued', 'message': 'Video subido. Iniciando motor AI...'}
    
    # Run the background process
    thread = threading.Thread(target=bg_process, args=(job_id, input_path, filename, mode, source, target))
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(jobs[job_id])

@app.route('/download/<job_id>')
def download(job_id):
    if job_id not in jobs or jobs[job_id]['status'] != 'done':
        return "File not ready or not found", 404
    
    if 'result_file' in jobs[job_id]:
        # Download dubbed video
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], jobs[job_id]['result_file'])
        return send_file(file_path, as_attachment=True)
    return "Not a valid download path", 400

@app.route('/download_clip/<job_id>/<filename>')
def download_clip(job_id, filename):
    if job_id not in jobs or jobs[job_id]['status'] != 'done':
        return "File not ready", 404
        
    folder = jobs[job_id].get('result_folder')
    if not folder:
        return "Clips not found", 404
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
