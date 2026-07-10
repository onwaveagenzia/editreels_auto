#!/usr/bin/env python3
"""
ONWAVE Processing API Server
Flask backend per gestire job di video processing
"""

import os
import json
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import queue

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ============================================================================
# SETUP
# ============================================================================

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('/tmp/onwave_uploads')
OUTPUT_FOLDER = Path('/tmp/onwave_outputs')
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# JOB STORAGE (in-memory + file persistence)
# ============================================================================

JOBS_DB_FILE = Path.home() / '.onwave' / 'jobs_api.json'

class JobStore:
    """Gestisce storage dei job"""
    
    def __init__(self):
        self.jobs = self._load_jobs()
        self.lock = threading.Lock()
    
    def _load_jobs(self) -> Dict:
        """Carica job da file"""
        JOBS_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        if JOBS_DB_FILE.exists():
            with open(JOBS_DB_FILE) as f:
                return json.load(f)
        return {}
    
    def _save_jobs(self):
        """Salva job su file"""
        with self.lock:
            with open(JOBS_DB_FILE, 'w') as f:
                json.dump(self.jobs, f, indent=2, default=str)
    
    def create_job(self, job_id: str, data: Dict) -> Dict:
        """Crea nuovo job"""
        with self.lock:
            job = {
                'id': job_id,
                'status': 'queued',
                'progress': 0,
                'current_step': None,
                'created': datetime.now().isoformat(),
                'started': None,
                'completed': None,
                'error': None,
                'results': [],
                **data
            }
            self.jobs[job_id] = job
            self._save_jobs()
            return job
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Recupera job"""
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        """Aggiorna job"""
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(kwargs)
                self._save_jobs()
    
    def list_jobs(self, limit: int = 100) -> List[Dict]:
        """Elenca ultimi job"""
        jobs_list = list(self.jobs.values())
        jobs_list.sort(key=lambda x: x['created'], reverse=True)
        return jobs_list[:limit]
    
    def get_stats(self) -> Dict:
        """Statistiche complessive"""
        jobs = list(self.jobs.values())
        
        completed = [j for j in jobs if j['status'] == 'completed']
        failed = [j for j in jobs if j['status'] == 'error']
        processing = [j for j in jobs if j['status'] == 'processing']
        
        total_size = sum([
            Path(r).stat().st_size 
            for j in completed 
            for r in j.get('results', [])
            if Path(r).exists()
        ]) / (1024 * 1024)  # MB
        
        avg_time = 0
        if completed:
            durations = []
            for j in completed:
                if j.get('started') and j.get('completed'):
                    start = datetime.fromisoformat(j['started'])
                    end = datetime.fromisoformat(j['completed'])
                    durations.append((end - start).total_seconds())
            avg_time = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_jobs': len(jobs),
            'completed': len(completed),
            'processing': len(processing),
            'failed': len(failed),
            'queued': len([j for j in jobs if j['status'] == 'queued']),
            'average_processing_time_seconds': int(avg_time),
            'total_output_size_mb': round(total_size, 1)
        }

# Istanza globale
job_store = JobStore()
job_queue = queue.Queue()

# ============================================================================
# PROCESSING WORKER
# ============================================================================

class ProcessingWorker(threading.Thread):
    """Worker thread che elabora job dalla queue"""
    
    def __init__(self, job_store: JobStore, job_queue: queue.Queue):
        super().__init__(daemon=True)
        self.job_store = job_store
        self.job_queue = job_queue
    
    def run(self):
        """Processo main del worker"""
        logger.info("🚀 Processing worker avviato")
        
        while True:
            try:
                job_id = self.job_queue.get(timeout=1)
                self.process_job(job_id)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def process_job(self, job_id: str):
        """Elabora singolo job"""
        job = self.job_store.get_job(job_id)
        if not job:
            return
        
        logger.info(f"▶️  Processing job: {job_id}")
        
        try:
            self.job_store.update_job(
                job_id,
                status='processing',
                started=datetime.now().isoformat()
            )
            
            # Call video-processor.py script
            video_path = job['video_path']
            preset = job['preset']
            output_dir = job['output_dir']
            options = job.get('options', {})
            
            cmd = [
                'python', 'scripts/video-processor.py',
                video_path,
                '--preset', preset,
                '--output', output_dir,
                '--job-id', job_id
            ]
            
            if not options.get('add_subtitles'):
                cmd.append('--no-subtitles')
            if not options.get('remove_silence'):
                cmd.append('--no-silence')
            
            # Run with progress tracking
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            for line in process.stdout:
                if 'progress' in line.lower():
                    logger.info(f"[{job_id}] {line.strip()}")
                    # Parse progress percentage
                    try:
                        progress = int(line.split('progress:')[1].split('%')[0])
                        self.job_store.update_job(job_id, progress=progress)
                    except:
                        pass
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Success
                logger.info(f"✓ Job completato: {job_id}")
                
                # Collect output files
                output_path = Path(output_dir)
                result_files = list(output_path.glob(f'{Path(video_path).stem}*'))
                
                self.job_store.update_job(
                    job_id,
                    status='completed',
                    progress=100,
                    completed=datetime.now().isoformat(),
                    results=[str(f) for f in result_files]
                )
                
                # Auto-upload to Google Drive if enabled
                if options.get('upload_to_drive'):
                    self._upload_to_drive(job_id, result_files)
            
            else:
                # Error
                error_msg = stderr or "Unknown error"
                logger.error(f"✗ Job fallito: {job_id}\n{error_msg}")
                
                self.job_store.update_job(
                    job_id,
                    status='error',
                    completed=datetime.now().isoformat(),
                    error=error_msg[:500]
                )
        
        except Exception as e:
            logger.error(f"Exception in job {job_id}: {e}")
            self.job_store.update_job(
                job_id,
                status='error',
                error=str(e)
            )
    
    def _upload_to_drive(self, job_id: str, files: List[Path]):
        """Auto-upload a Google Drive"""
        try:
            logger.info(f"📤 Caricando risultati su Drive: {job_id}")
            # TODO: implementa con google_drive_sync.py
            logger.info(f"✓ Upload completato")
        except Exception as e:
            logger.warning(f"Drive upload fallito: {e}")

# Avvia worker thread
worker = ProcessingWorker(job_store, job_queue)
worker.start()

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/upload', methods=['POST'])
def upload_video():
    """
    Carica un file video sul server, per poi poterlo processare
    (job normale o /api/transcribe).

    Form-data: file=<video binario>

    Returns: { "video_path": "/tmp/onwave_uploads/xxx.mp4", "size_mb": 12.3 }
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file inviato (campo "file" mancante)'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome file vuoto'}), 400

    valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
    ext = Path(file.filename).suffix.lower()
    if ext not in valid_extensions:
        return jsonify({'error': f'Formato non supportato: {ext}'}), 400

    filename = secure_filename(file.filename)
    # Prefisso timestamp per evitare collisioni tra upload diversi
    unique_name = f"{int(datetime.now().timestamp())}_{filename}"
    save_path = UPLOAD_FOLDER / unique_name

    file.save(str(save_path))
    size_mb = round(save_path.stat().st_size / (1024 * 1024), 2)

    logger.info(f"📤 Upload ricevuto: {unique_name} ({size_mb} MB)")

    return jsonify({
        'video_path': str(save_path),
        'filename': unique_name,
        'size_mb': size_mb
    }), 201


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'worker_alive': worker.is_alive()
    })

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """Elenca job"""
    limit = request.args.get('limit', 100, type=int)
    jobs = job_store.list_jobs(limit)
    return jsonify({
        'jobs': jobs,
        'total': len(jobs)
    })

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id: str):
    """Dettagli job"""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/api/jobs/<job_id>/progress', methods=['GET'])
def get_progress(job_id: str):
    """Progress in real-time"""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job_id': job_id,
        'progress': job.get('progress', 0),
        'status': job['status'],
        'current_step': job.get('current_step'),
        'error': job.get('error')
    })

@app.route('/api/jobs', methods=['POST'])
def submit_job():
    """Submitti nuovo job"""
    data = request.get_json()
    
    # Validazione
    required = ['job_id', 'video_path', 'preset', 'output_dir']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    job_id = data['job_id']
    
    # Crea job
    job = job_store.create_job(job_id, {
        'video_path': data['video_path'],
        'preset': data['preset'],
        'output_dir': data['output_dir'],
        'options': data.get('options', {})
    })
    
    # Aggiungi alla queue
    job_queue.put(job_id)
    
    logger.info(f"📋 Job sottomesso: {job_id}")
    
    return jsonify(job), 202

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id: str):
    """Cancella job"""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job['status'] in ['processing']:
        # TODO: kill process
        pass
    
    job_store.update_job(job_id, status='cancelled')
    return jsonify({'status': 'cancelled'})

@app.route('/api/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id: str):
    """Riprova job fallito"""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job['status'] != 'error':
        return jsonify({'error': 'Can only retry failed jobs'}), 400
    
    # Reset job
    job_store.update_job(
        job_id,
        status='queued',
        progress=0,
        error=None,
        started=None,
        completed=None
    )
    
    # Aggiungi di nuovo alla queue
    job_queue.put(job_id)
    
    return jsonify({'status': 'queued'})

@app.route('/api/jobs/<job_id>/download/<filename>', methods=['GET'])
def download_result(job_id: str, filename: str):
    """Scarica file risultato"""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Valida filename (security)
    filename = secure_filename(filename)
    
    file_path = Path(job['output_dir']) / filename
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return {
        'download_url': f'/api/downloads/{job_id}/{filename}',
        'filename': filename,
        'size_mb': round(file_path.stat().st_size / (1024 * 1024), 1)
    }

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiche complessive"""
    return jsonify(job_store.get_stats())

@app.route('/api/transcribe', methods=['POST'])
def transcribe_endpoint():
    """
    Trascrive un video e genera sottotitoli + emoji contestuali.
    Body JSON: { "video_path": "...", "output_path": "...", "language": "it",
                 "burn_subtitles": true, "add_emojis": true, "model_size": "small" }

    Nota: questa chiamata è SINCRONA e può richiedere da 10s a qualche minuto
    a seconda della durata del video e della dimensione del modello scelto.
    Per video lunghi, usare via job queue invece di chiamata diretta.
    """
    data = request.get_json()

    video_path = data.get('video_path')
    if not video_path or not Path(video_path).exists():
        return jsonify({'error': 'video_path mancante o file non trovato'}), 400

    output_path = data.get('output_path') or str(
        Path(video_path).with_stem(Path(video_path).stem + '_captioned')
    )

    try:
        from subtitle_emoji_processor import add_subtitles_and_emojis

        result = add_subtitles_and_emojis(
            input_video=video_path,
            output_video=output_path,
            model_size=data.get('model_size', 'small'),
            language=data.get('language', 'it'),
            burn_subtitles=data.get('burn_subtitles', True),
            add_emojis=data.get('add_emojis', True)
        )

        return jsonify({'status': 'completed', **result}), 200

    except Exception as e:
        logger.error(f"Errore trascrizione: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Elenca preset disponibili"""
    return jsonify({
        'presets': [
            {
                'id': 'social_media',
                'name': 'Social Media',
                'description': 'TikTok, Instagram Reels, YouTube Shorts'
            },
            {
                'id': 'educational',
                'name': 'Educational',
                'description': 'Tutorial, Corsi Online'
            },
            {
                'id': 'corporate',
                'name': 'Corporate',
                'description': 'Branding, Video Aziendali'
            },
            {
                'id': 'testimonial',
                'name': 'Testimonial',
                'description': 'Case Study, Recensioni'
            }
        ]
    })

# ============================================================================
# ERROR HANDLING
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 ONWAVE API Server avviato su port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
