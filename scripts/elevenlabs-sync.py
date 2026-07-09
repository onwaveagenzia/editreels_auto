#!/usr/bin/env python3
"""
ONWAVE ElevenLabs Integration
Genera voiceover di qualità cinema e sincronizza con video.
"""

import os
import json
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "YOUR_ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

@dataclass
class VoiceSettings:
    """Configurazione voce ElevenLabs"""
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default: Bella (neutral female)
    stability: float = 0.5
    similarity_boost: float = 0.75
    model_id: str = "eleven_monolingual_v1"

# ============================================================================
# ELEVENLABS API CLIENT
# ============================================================================

class ElevenLabsClient:
    """Client per ElevenLabs API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ELEVENLABS_BASE_URL
        self.headers = {"xi-api-key": api_key}
    
    def list_voices(self) -> List[Dict]:
        """Elenca tutte le voci disponibili"""
        try:
            url = f"{self.base_url}/voices"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["voices"]
        except Exception as e:
            logger.error(f"Errore listaggio voci: {e}")
            return []
    
    def text_to_speech(
        self,
        text: str,
        voice_settings: VoiceSettings,
        output_path: str
    ) -> bool:
        """Converte testo in audio sintetizzato"""
        try:
            url = f"{self.base_url}/text-to-speech/{voice_settings.voice_id}"
            
            payload = {
                "text": text,
                "model_id": voice_settings.model_id,
                "voice_settings": {
                    "stability": voice_settings.stability,
                    "similarity_boost": voice_settings.similarity_boost,
                }
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Audio sintetizzato: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore text-to-speech: {e}")
            return False
    
    def get_usage(self) -> Dict:
        """Verifica uso API e crediti"""
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Errore verifica usage: {e}")
            return {}

# ============================================================================
# VOICE PROFILE MANAGER
# ============================================================================

class VoiceProfileManager:
    """Gestisce profili vocali predefiniti per ONWAVE"""
    
    PROFILES = {
        "professional": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Bella
            "stability": 0.5,
            "similarity_boost": 0.75,
            "description": "Voce professionale, neutra, per corporate video"
        },
        "warm": {
            "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Duane
            "stability": 0.4,
            "similarity_boost": 0.85,
            "description": "Voce calda, accogliente, per tutorial/educational"
        },
        "energetic": {
            "voice_id": "p305z4z21i11qg30h92h",  # Andrea
            "stability": 0.6,
            "similarity_boost": 0.8,
            "description": "Voce energica, dinamica, per social media"
        },
        "deep": {
            "voice_id": "onwK4e9ZLuTAKqWW03F9",  # Adam
            "stability": 0.7,
            "similarity_boost": 0.7,
            "description": "Voce profonda, autorevole, per narrazioni"
        }
    }
    
    @staticmethod
    def get_voice_settings(profile: str) -> Optional[VoiceSettings]:
        """Carica profilo voce"""
        if profile not in VoiceProfileManager.PROFILES:
            logger.warning(f"Profilo {profile} non trovato, uso 'professional'")
            profile = "professional"
        
        p = VoiceProfileManager.PROFILES[profile]
        return VoiceSettings(
            voice_id=p["voice_id"],
            stability=p["stability"],
            similarity_boost=p["similarity_boost"]
        )
    
    @staticmethod
    def list_profiles() -> Dict:
        """Elenca profili disponibili"""
        return {
            name: {
                "description": data["description"],
                "stability": data["stability"],
                "similarity": data["similarity_boost"]
            }
            for name, data in VoiceProfileManager.PROFILES.items()
        }

# ============================================================================
# AUDIO SYNC
# ============================================================================

class AudioSync:
    """Sincronizza audio sintetizzato con video"""
    
    @staticmethod
    def measure_audio_duration(audio_path: str) -> float:
        """Calcola durata audio con ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Errore misura audio: {e}")
            return 0
    
    @staticmethod
    def merge_audio_video(
        video_path: str,
        audio_path: str,
        output_path: str,
        remove_original_audio: bool = True
    ) -> bool:
        """Sostituisce o mescola audio nel video"""
        try:
            if remove_original_audio:
                # Rimuovi audio originale e aggiungi nuovo
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-n", output_path
                ]
            else:
                # Mescola audio (original + voiceover)
                cmd = [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                    "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]",
                    "-map", "0:v:0",
                    "-map", "[a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-n", output_path
                ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ Audio sincronizzato: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore sync audio: {e}")
            return False

# ============================================================================
# SCRIPT PROCESSOR
# ============================================================================

class VoiceoverProcessor:
    """Processa script e genera voiceover sincrono"""
    
    def __init__(self, api_key: str):
        self.client = ElevenLabsClient(api_key)
    
    def process_script(
        self,
        video_path: str,
        script_text: str,
        voice_profile: str = "professional",
        output_dir: str = "./output",
        keep_original_audio: bool = False
    ) -> Dict:
        """Workflow completo: testo → audio sintetizzato → merge video"""
        
        print(f"\n{'='*60}")
        print(f"🎙️  ONWAVE Voiceover Generator")
        print(f"{'='*60}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. VALIDAZIONE
        print("✓ Fase 1: Validazione...")
        voice_settings = VoiceProfileManager.get_voice_settings(voice_profile)
        print(f"   ✓ Profilo voce: {voice_profile}")
        print(f"   ✓ Lunghezza script: {len(script_text)} caratteri")
        
        # 2. SINTESI VOCALE
        print("\n🎤 Fase 2: Sintesi Vocale...")
        audio_output = os.path.join(output_dir, "voiceover.mp3")
        
        success = self.client.text_to_speech(
            script_text,
            voice_settings,
            audio_output
        )
        
        if not success:
            return {"error": "Errore sintesi vocale"}
        
        # Misura durata
        audio_duration = AudioSync.measure_audio_duration(audio_output)
        print(f"   ✓ Audio generato: {audio_duration:.1f}s")
        
        # 3. SINCRONIZZAZIONE
        print("\n🎬 Fase 3: Sincronizzazione Audio-Video...")
        final_video = os.path.join(output_dir, "video_with_voiceover.mp4")
        
        sync_success = AudioSync.merge_audio_video(
            video_path,
            audio_output,
            final_video,
            remove_original_audio=not keep_original_audio
        )
        
        if not sync_success:
            return {"error": "Errore sincronizzazione audio"}
        
        # 4. REPORT
        print(f"\n{'='*60}")
        print("✅ Voiceover Completato!")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "video_path": final_video,
            "audio_duration_seconds": audio_duration,
            "voice_profile": voice_profile,
            "character_count": len(script_text),
            "output_directory": output_dir
        }

# ============================================================================
# CLI
# ============================================================================

def show_voices():
    """Mostra voci disponibili"""
    profiles = VoiceProfileManager.list_profiles()
    print("\n📢 Profili Voce Disponibili:\n")
    for name, data in profiles.items():
        print(f"  • {name.upper()}")
        print(f"    {data['description']}")
        print(f"    Stabilità: {data['stability']}, Similarità: {data['similarity']}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Uso:
  python elevenlabs-sync.py --list-voices
  python elevenlabs-sync.py <video_path> --script <script_file> [--voice PROFILE] [--keep-original]
  python elevenlabs-sync.py <video_path> --text "Testo diretto" [--voice PROFILE]
        """)
        sys.exit(1)
    
    # Comandi speciali
    if sys.argv[1] == "--list-voices":
        show_voices()
        sys.exit(0)
    
    # Processa voiceover
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ Video non trovato: {video_path}")
        sys.exit(1)
    
    # Leggi script
    script_text = ""
    voice_profile = "professional"
    keep_original = False
    
    if "--script" in sys.argv:
        idx = sys.argv.index("--script")
        script_file = sys.argv[idx + 1]
        with open(script_file, 'r', encoding='utf-8') as f:
            script_text = f.read()
    elif "--text" in sys.argv:
        idx = sys.argv.index("--text")
        script_text = sys.argv[idx + 1]
    else:
        print("❌ Fornisci --script <file> o --text '<testo>'")
        sys.exit(1)
    
    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        voice_profile = sys.argv[idx + 1]
    
    if "--keep-original" in sys.argv:
        keep_original = True
    
    # Processa
    processor = VoiceoverProcessor(ELEVENLABS_API_KEY)
    result = processor.process_script(
        video_path,
        script_text,
        voice_profile=voice_profile,
        keep_original_audio=keep_original
    )
    
    # Output
    print("\n📊 Report:")
    print(json.dumps(result, indent=2))
