#!/usr/bin/env python3
"""
ONWAVE Google Drive Watcher
Autenticazione via Service Account (nessun browser richiesto - adatto a server headless).

Monitora una cartella Drive per nuovi video, li scarica, li elabora
con il preset scelto, e carica il risultato in una cartella di output.
"""

import os
import io
import json
import time
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Set

logger = logging.getLogger(__name__)

_drive_service = None
_processed_file_ids: Set[str] = set()


# ============================================================================
# AUTENTICAZIONE (Service Account)
# ============================================================================

def get_drive_service():
    """
    Costruisce il client Google Drive autenticato via Service Account.
    Richiede la variabile d'ambiente GOOGLE_SERVICE_ACCOUNT_JSON
    (contenuto completo del file JSON della chiave, come stringa).
    """
    global _drive_service
    if _drive_service is not None:
        return _drive_service

    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw_json:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON non impostata. "
            "Serve il contenuto del file JSON del Service Account come variabile d'ambiente."
        )

    info = json.loads(raw_json)
    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)

    _drive_service = build("drive", "v3", credentials=creds)
    logger.info("✓ Autenticato con Google Drive (Service Account)")
    return _drive_service


# ============================================================================
# OPERAZIONI DRIVE
# ============================================================================

def list_videos_in_folder(folder_id: str) -> List[Dict]:
    """Elenca i file video presenti in una cartella Drive"""
    service = get_drive_service()

    query = f"'{folder_id}' in parents and trashed=false and mimeType contains 'video'"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, size, createdTime)',
        pageSize=50
    ).execute()

    return results.get('files', [])


def download_file(file_id: str, dest_path: str) -> None:
    """Scarica un file da Drive"""
    from googleapiclient.http import MediaIoBaseDownload

    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


def upload_file(local_path: str, folder_id: str) -> Optional[str]:
    """Carica un file su Drive, restituisce l'ID del file caricato"""
    from googleapiclient.http import MediaFileUpload

    service = get_drive_service()
    file_metadata = {'name': Path(local_path).name, 'parents': [folder_id]}
    media = MediaFileUpload(local_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return file.get('id')


def create_folder(name: str, parent_id: str) -> str:
    """Crea una sottocartella su Drive (es. per organizzare i risultati per job)"""
    service = get_drive_service()
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


# ============================================================================
# WATCHER LOOP (background thread)
# ============================================================================

def watch_and_process(
    input_folder_id: str,
    output_folder_id: str,
    upload_dir: Path,
    process_callback,
    preset: str = "social_media",
    poll_interval: int = 60
):
    """
    Loop continuo che:
    1. Controlla la cartella input per nuovi video
    2. Li scarica
    3. Chiama process_callback(video_path, preset) -> output_path
    4. Carica il risultato nella cartella output
    5. Aspetta poll_interval secondi e ripete

    Va lanciato in un thread separato (daemon=True) all'avvio del server.
    """
    logger.info(f"👀 Drive Watcher avviato (poll ogni {poll_interval}s)")

    while True:
        try:
            videos = list_videos_in_folder(input_folder_id)
            new_videos = [v for v in videos if v['id'] not in _processed_file_ids]

            if new_videos:
                logger.info(f"🎬 Trovati {len(new_videos)} nuovi video su Drive")

            for video in new_videos:
                file_id = video['id']
                file_name = video['name']

                try:
                    local_input = str(upload_dir / f"drive_{file_id}_{file_name}")
                    logger.info(f"⬇️  Download: {file_name}")
                    download_file(file_id, local_input)

                    local_output = str(upload_dir / f"drive_{file_id}_processed.mp4")
                    logger.info(f"⚙️  Elaborazione: {file_name} (preset: {preset})")
                    process_callback(local_input, local_output, preset)

                    logger.info(f"⬆️  Upload risultato: {file_name}")
                    upload_file(local_output, output_folder_id)

                    _processed_file_ids.add(file_id)
                    logger.info(f"✓ Completato: {file_name}")

                    # Pulizia file locali
                    Path(local_input).unlink(missing_ok=True)
                    Path(local_output).unlink(missing_ok=True)

                except Exception as e:
                    logger.error(f"❌ Errore processando {file_name}: {e}")
                    # Segna comunque come processato per non ritentare in loop infinito
                    _processed_file_ids.add(file_id)

        except Exception as e:
            logger.error(f"❌ Errore nel ciclo watcher: {e}")

        time.sleep(poll_interval)


def start_watcher_thread(
    input_folder_id: str,
    output_folder_id: str,
    upload_dir: Path,
    process_callback,
    preset: str = "social_media",
    poll_interval: int = 60
) -> threading.Thread:
    """Avvia il watcher in un thread background (non bloccante)"""
    thread = threading.Thread(
        target=watch_and_process,
        args=(input_folder_id, output_folder_id, upload_dir, process_callback, preset, poll_interval),
        daemon=True
    )
    thread.start()
    return thread
