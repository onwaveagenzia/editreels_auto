#!/usr/bin/env python3
"""
ONWAVE Google Drive Sync
Auto-upload videos, auto-download results, watch for new files
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import logging

try:
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as UserCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    import io
except ImportError:
    print("⚠️  Installa dipendenze: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = Path.home() / '.onwave' / 'google_credentials.json'
TOKEN_FILE = Path.home() / '.onwave' / 'google_token.json'
SYNC_DB_FILE = Path.home() / '.onwave' / 'sync_db.json'

# ============================================================================
# GOOGLE DRIVE CLIENT
# ============================================================================

class GoogleDriveClient:
    """Client per Google Drive API"""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Autentica con Google Drive"""
        creds = None
        
        # Carica token salvato
        if TOKEN_FILE.exists():
            creds = UserCredentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # Se no token valido, richiedi autenticazione
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # First-time setup: usa OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Salva token per usi futuri
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✓ Autenticato con Google Drive")
    
    def list_files(self, folder_id: str, query: Optional[str] = None) -> List[Dict]:
        """Elenca file in cartella"""
        try:
            q = f"'{folder_id}' in parents and trashed=false"
            if query:
                q += f" and {query}"
            
            results = self.service.files().list(
                q=q,
                spaces='drive',
                fields='files(id, name, mimeType, size, createdTime, modifiedTime)',
                pageSize=100
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Errore listaggio: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str, output_path: str) -> bool:
        """Scarica file da Google Drive"""
        try:
            logger.info(f"Scaricando: {file_name}")
            
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')
            
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    logger.info(f"  {percent}% completato")
            
            fh.close()
            logger.info(f"✓ Scaricato: {file_name}")
            return True
        
        except Exception as e:
            logger.error(f"Errore download: {e}")
            return False
    
    def upload_file(self, file_path: str, folder_id: str, mime_type: Optional[str] = None) -> Optional[str]:
        """Carica file su Google Drive"""
        try:
            file_name = Path(file_path).name
            logger.info(f"Caricando: {file_name}")
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True, mimetype=mime_type)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"✓ Caricato: {file_name}")
            return file.get('id')
        
        except Exception as e:
            logger.error(f"Errore upload: {e}")
            return None
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Crea cartella su Google Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            logger.info(f"✓ Cartella creata: {folder_name}")
            return folder.get('id')
        
        except Exception as e:
            logger.error(f"Errore creazione cartella: {e}")
            return None
    
    def share_file(self, file_id: str, email: str, role: str = 'reader') -> bool:
        """Condividi file via email"""
        try:
            self.service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                }
            ).execute()
            
            logger.info(f"✓ Condiviso con: {email}")
            return True
        
        except Exception as e:
            logger.error(f"Errore condivisione: {e}")
            return False

# ============================================================================
# SYNC MANAGER
# ============================================================================

class SyncManager:
    """Gestisce sincronizzazione con Google Drive"""
    
    def __init__(self, drive_client: GoogleDriveClient, config: Dict):
        self.drive = drive_client
        self.config = config
        self.input_folder_id = config.get('google_drive_input_folder_id')
        self.output_folder_id = config.get('google_drive_output_folder_id')
        self.local_input_dir = Path(config.get('local_input_dir', '/tmp/onwave_input'))
        self.local_output_dir = Path(config.get('local_output_dir', '/tmp/onwave_output'))
        self.sync_db = self._load_sync_db()
    
    def _load_sync_db(self) -> Dict:
        """Carica database di sincronizzazione"""
        if SYNC_DB_FILE.exists():
            with open(SYNC_DB_FILE) as f:
                return json.load(f)
        return {'processed_files': []}
    
    def _save_sync_db(self):
        """Salva database di sincronizzazione"""
        SYNC_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNC_DB_FILE, 'w') as f:
            json.dump(self.sync_db, f, indent=2)
    
    def watch_input_folder(self):
        """Monitora cartella input per nuovi video"""
        logger.info(f"👀 Monitoraggio cartella input: {self.input_folder_id}")
        
        files = self.drive.list_files(
            self.input_folder_id,
            query="mimeType contains 'video'"
        )
        
        new_files = []
        for file in files:
            if file['id'] not in self.sync_db['processed_files']:
                new_files.append(file)
                logger.info(f"🎬 Nuovo video trovato: {file['name']}")
        
        return new_files
    
    def download_video(self, file_id: str, file_name: str) -> bool:
        """Scarica video da input folder"""
        self.local_input_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.local_input_dir / file_name
        
        success = self.drive.download_file(file_id, file_name, str(output_path))
        
        if success:
            self.sync_db['processed_files'].append(file_id)
            self._save_sync_db()
        
        return success
    
    def upload_results(self, job_id: str, result_files: List[str]):
        """Carica risultati a output folder"""
        logger.info(f"📤 Caricamento risultati per job: {job_id}")
        
        # Crea subfolder per job
        job_folder_id = self.drive.create_folder(job_id, self.output_folder_id)
        
        for file_path in result_files:
            if Path(file_path).exists():
                self.drive.upload_file(file_path, job_folder_id)
        
        logger.info(f"✓ Risultati caricati in: {job_id}")
        return job_folder_id
    
    def sync_cycle(self, process_callback):
        """Ciclo di sincronizzazione continua"""
        logger.info("🔄 Avvio ciclo di sincronizzazione...")
        
        while True:
            try:
                # Controlla nuovi video in input
                new_videos = self.watch_input_folder()
                
                for video in new_videos:
                    file_id = video['id']
                    file_name = video['name']
                    
                    # Scarica video
                    if self.download_video(file_id, file_name):
                        local_path = self.local_input_dir / file_name
                        
                        # Process video
                        logger.info(f"⚙️  Processing: {file_name}")
                        result_files = process_callback(str(local_path))
                        
                        # Upload results
                        if result_files:
                            job_id = Path(file_name).stem
                            self.upload_results(job_id, result_files)
                
                # Wait before next check
                wait_seconds = self.config.get('sync_interval_seconds', 300)
                logger.info(f"⏳ Prossima verifica tra {wait_seconds}s...")
                time.sleep(wait_seconds)
            
            except KeyboardInterrupt:
                logger.info("🛑 Sincronizzazione fermata")
                break
            except Exception as e:
                logger.error(f"Errore ciclo sincronizzazione: {e}")
                time.sleep(60)

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================

def setup_google_drive():
    """Setup iniziale di Google Drive"""
    import webbrowser
    
    print("\n[🔐 Google Drive Setup]")
    print("=" * 50)
    
    print("\n1. Vai a: https://console.cloud.google.com/")
    print("2. Crea nuovo progetto")
    print("3. Abilita Google Drive API")
    print("4. Crea 'OAuth 2.0 Client ID' (Desktop app)")
    print("5. Download credentials.json")
    print(f"6. Salva in: {CREDENTIALS_FILE}")
    print("\nPer per scaricare file di prova:")
    
    # Create test folders
    drive = GoogleDriveClient()
    
    input_folder_id = drive.create_folder('ONWAVE_Input')
    output_folder_id = drive.create_folder('ONWAVE_Output')
    
    print(f"\n📁 Input Folder ID: {input_folder_id}")
    print(f"📁 Output Folder ID: {output_folder_id}")
    
    # Save to config
    config_path = Path.home() / '.onwave' / 'config.json'
    config = json.load(open(config_path)) if config_path.exists() else {}
    
    config.update({
        'google_drive_enabled': True,
        'google_drive_input_folder_id': input_folder_id,
        'google_drive_output_folder_id': output_folder_id
    })
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Setup completato!")
    print(f"Config salvata: {config_path}")

# ============================================================================
# CLI COMMANDS
# ============================================================================

import click

@click.group()
def drive_cli():
    """Google Drive management"""
    pass

@drive_cli.command()
def setup():
    """Setup Google Drive integration"""
    setup_google_drive()

@drive_cli.command()
@click.option('--input-folder', help='Input folder ID')
@click.option('--output-folder', help='Output folder ID')
@click.option('--watch-interval', default=300, help='Sync interval (seconds)')
def watch(input_folder: str, output_folder: str, watch_interval: int):
    """Watch for new videos and auto-process"""
    
    config_path = Path.home() / '.onwave' / 'config.json'
    config = json.load(open(config_path)) if config_path.exists() else {}
    
    config.update({
        'google_drive_input_folder_id': input_folder or config.get('google_drive_input_folder_id'),
        'google_drive_output_folder_id': output_folder or config.get('google_drive_output_folder_id'),
        'sync_interval_seconds': watch_interval
    })
    
    drive = GoogleDriveClient()
    sync = SyncManager(drive, config)
    
    # Define process callback
    def process_video(video_path: str):
        """Callback per processare video"""
        # TODO: integra con video-processor.py
        logger.info(f"Processing: {video_path}")
        return []
    
    # Start watching
    sync.sync_cycle(process_video)

if __name__ == '__main__':
    drive_cli()
