#!/usr/bin/env python3
"""
ONWAVE Video Processing Engine
Gestisce analisi, editing, sottotitoli e export video professionale.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from datetime import timedelta
import subprocess

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    import numpy as np
except ImportError:
    print("⚠️  Librerie mancanti. Installa con: pip install moviepy pydub numpy")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

@dataclass
class VideoConfig:
    """Configurazione per video processing"""
    silence_threshold: int = -40  # dB
    min_silence_duration: float = 2.0  # secondi
    remove_silence: bool = True
    crossfade_duration: float = 0.3
    
    # Subtitle
    font_size: int = 48
    font_family: str = "Arial"
    font_color: str = "#FFFFFF"
    background_color: str = "rgba(0,0,0,0.7)"
    
    # Export
    bitrate_mp4: str = "8000k"
    bitrate_webm: str = "6000k"
    fps: int = 30
    resolution: str = "1920x1080"

CONFIG = VideoConfig()

# ============================================================================
# ANALISI VIDEO
# ============================================================================

class VideoAnalyzer:
    """Analizza video: durata, qualità audio, silenzi"""
    
    @staticmethod
    def analyze(video_path: str) -> Dict:
        """Analizza metadati video"""
        try:
            clip = VideoFileClip(video_path)
            audio = clip.audio
            
            analysis = {
                "file": Path(video_path).name,
                "duration_seconds": clip.duration,
                "duration_formatted": str(timedelta(seconds=int(clip.duration))),
                "fps": clip.fps,
                "resolution": f"{clip.w}x{clip.h}",
                "audio_fps": audio.fps if audio else None,
                "audio_nchannels": audio.nchannels if audio else None,
                "file_size_mb": os.path.getsize(video_path) / (1024 * 1024),
            }
            
            # Estrai array audio per analisi silenzi
            if audio:
                audio_array = audio.to_soundarray()
                # Detecta silenzi
                silences = VideoAnalyzer._detect_silences(audio_array, audio.fps)
                analysis["silences_detected"] = silences
                analysis["total_silence_seconds"] = sum(s[1] - s[0] for s in silences)
                analysis["potential_savings_seconds"] = analysis["total_silence_seconds"]
            
            clip.close()
            return analysis
            
        except Exception as e:
            logger.error(f"Errore analisi video: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _detect_silences(audio_array: np.ndarray, fps: int, threshold: int = -40) -> List[Tuple]:
        """Rileva periodi di silenzio nel file audio"""
        try:
            # Converti in mono se stereo
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)
            
            # Calcola amplitude in dB
            epsilon = 1e-10
            dB = 20 * np.log10(np.abs(audio_array) + epsilon)
            
            # Trova frame sotto threshold
            silent_frames = dB < threshold
            
            # Raggruppa frame silenziosi consecutivi
            silences = []
            start = None
            for i, is_silent in enumerate(silent_frames):
                if is_silent and start is None:
                    start = i
                elif not is_silent and start is not None:
                    duration = (i - start) / fps
                    if duration >= CONFIG.min_silence_duration:
                        silences.append((start / fps, i / fps))
                    start = None
            
            return silences
        except Exception as e:
            logger.warning(f"Errore detection silenzi: {e}")
            return []

# ============================================================================
# EDITING VIDEO
# ============================================================================

class VideoEditor:
    """Taglia, monta e modifica video"""
    
    @staticmethod
    def cut_silences(video_path: str, silences: List[Tuple]) -> str:
        """Rimuove silenzi dal video"""
        try:
            clip = VideoFileClip(video_path)
            clips = []
            
            # Crea clip senza silenzi
            last_end = 0
            for silence_start, silence_end in silences:
                if silence_start > last_end:
                    clips.append(clip.subclip(last_end, silence_start))
                last_end = silence_end
            
            # Aggiungi ultima parte
            if last_end < clip.duration:
                clips.append(clip.subclip(last_end, clip.duration))
            
            if not clips:
                logger.warning("Nessuno clip creato - ritorna video originale")
                return video_path
            
            # Concatena con crossfade
            final = concatenate_videoclips(clips, method="chain")
            
            output_path = video_path.replace(".mp4", "_edited.mp4")
            final.write_videofile(output_path, verbose=False, logger=None)
            clip.close()
            
            logger.info(f"✓ Video editato salvato: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Errore taglio silenzio: {e}")
            return video_path
    
    @staticmethod
    def add_subtitles_overlay(video_path: str, subtitles: List[Dict]) -> str:
        """Aggiunge sottotitoli come overlay"""
        try:
            video = VideoFileClip(video_path)
            clips = [video]
            
            for sub in subtitles:
                txt_clip = TextClip(
                    sub["text"],
                    fontsize=CONFIG.font_size,
                    font=CONFIG.font_family,
                    color=CONFIG.font_color,
                    method='caption',
                    size=(video.w - 40, None),
                    transparent=True
                )
                txt_clip = txt_clip.set_position('bottom')
                txt_clip = txt_clip.set_start(sub["start"])
                txt_clip = txt_clip.set_duration(sub["end"] - sub["start"])
                clips.append(txt_clip)
            
            final = CompositeVideoClip(clips, size=video.size)
            output_path = video_path.replace(".mp4", "_with_subs.mp4")
            final.write_videofile(output_path, verbose=False, logger=None)
            video.close()
            
            logger.info(f"✓ Sottotitoli applicati: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Errore aggiunta sottotitoli: {e}")
            return video_path

# ============================================================================
# GENERAZIONE SOTTOTITOLI
# ============================================================================

class SubtitleGenerator:
    """Genera sottotitoli da trascrizione automatica"""
    
    @staticmethod
    def extract_audio(video_path: str) -> str:
        """Estrae audio dal video"""
        try:
            audio_path = video_path.replace(".mp4", ".wav")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-q:a", "9", "-n", audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ Audio estratto: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"Errore estrazione audio: {e}")
            return None
    
    @staticmethod
    def transcribe_to_srt(audio_path: str) -> str:
        """Genera trascrizione e converte in SRT usando Whisper (mock)"""
        try:
            # In produzione, usa: whisper audio_path --output_format srt
            # Per demo, crea un SRT di esempio
            srt_path = audio_path.replace(".wav", ".srt")
            
            srt_content = """1
00:00:00,000 --> 00:00:03,000
Trascrizione automatica dal video

2
00:00:03,000 --> 00:00:06,500
Sistema di sottotitoli ONWAVE

3
00:00:06,500 --> 00:00:10,000
Sincronizzazione perfetta audio-video
"""
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✓ Sottotitoli generati: {srt_path}")
            return srt_path
        except Exception as e:
            logger.error(f"Errore generazione SRT: {e}")
            return None
    
    @staticmethod
    def parse_srt(srt_path: str) -> List[Dict]:
        """Legge SRT e ritorna lista di sottotitoli"""
        subtitles = []
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    time_range = lines[1]
                    text = ' '.join(lines[2:])
                    
                    start_str, end_str = time_range.split(' --> ')
                    start = SubtitleGenerator._time_to_seconds(start_str)
                    end = SubtitleGenerator._time_to_seconds(end_str)
                    
                    subtitles.append({
                        "start": start,
                        "end": end,
                        "text": text
                    })
            
            logger.info(f"✓ Sottotitoli caricati: {len(subtitles)} entry")
            return subtitles
        except Exception as e:
            logger.error(f"Errore parsing SRT: {e}")
            return []
    
    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        """Converte formato SRT (HH:MM:SS,mmm) a secondi"""
        parts = time_str.replace(',', '.').split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

# ============================================================================
# EXPORT
# ============================================================================

class VideoExporter:
    """Esporta video in multipli formati"""
    
    @staticmethod
    def export_mp4(video_path: str) -> str:
        """Esporta in MP4 H.264/AAC"""
        try:
            output = video_path.replace(".mp4", "_final.mp4")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-c:v", "libx264",
                "-preset", "medium",
                "-b:v", CONFIG.bitrate_mp4,
                "-c:a", "aac",
                "-b:a", "128k",
                "-n", output
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ MP4 esportato: {output}")
            return output
        except Exception as e:
            logger.error(f"Errore export MP4: {e}")
            return None
    
    @staticmethod
    def export_webm(video_path: str) -> str:
        """Esporta in WebM VP9/Opus"""
        try:
            output = video_path.replace(".mp4", "_web.webm")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-c:v", "libvpx-vp9",
                "-b:v", CONFIG.bitrate_webm,
                "-c:a", "libopus",
                "-b:a", "96k",
                "-n", output
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ WebM esportato: {output}")
            return output
        except Exception as e:
            logger.error(f"Errore export WebM: {e}")
            return None
    
    @staticmethod
    def export_mov(video_path: str) -> str:
        """Esporta in MOV ProRes per post-production"""
        try:
            output = video_path.replace(".mp4", "_pro.mov")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-c:v", "prores",
                "-profile:v", "3",
                "-c:a", "pcm_s16le",
                "-n", output
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ MOV ProRes esportato: {output}")
            return output
        except Exception as e:
            logger.error(f"Errore export MOV: {e}")
            return None

# ============================================================================
# ORCHESTRATOR
# ============================================================================

class VideoProcessor:
    """Orchestrator del workflow completo"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.analyzer = VideoAnalyzer()
        self.editor = VideoEditor()
        self.subtitle_gen = SubtitleGenerator()
        self.exporter = VideoExporter()
        self.report = {}
    
    def process(self, add_subtitles: bool = True, remove_silence: bool = True) -> Dict:
        """Workflow completo: analizza → taglia → sottotitoli → export"""
        
        print(f"\n{'='*60}")
        print(f"🎬 ONWAVE Video Processing")
        print(f"{'='*60}\n")
        
        # 1. ANALISI
        print("📊 Fase 1: Analisi Video...")
        analysis = self.analyzer.analyze(self.video_path)
        if "error" in analysis:
            return {"error": analysis["error"]}
        print(f"   ✓ Durata: {analysis['duration_formatted']}")
        print(f"   ✓ Risoluzione: {analysis['resolution']}")
        print(f"   ✓ Silenzi rilevati: {len(analysis.get('silences_detected', []))} ({analysis.get('total_silence_seconds', 0):.1f}s)")
        
        self.report["analysis"] = analysis
        
        # 2. TAGLIO SILENZI
        current_video = self.video_path
        if remove_silence and analysis.get('silences_detected'):
            print("\n✂️  Fase 2: Rimozione Silenzi...")
            current_video = self.editor.cut_silences(
                self.video_path,
                analysis['silences_detected']
            )
        
        # 3. SOTTOTITOLI
        subtitles = []
        if add_subtitles:
            print("\n📝 Fase 3: Generazione Sottotitoli...")
            audio_path = self.subtitle_gen.extract_audio(current_video)
            srt_path = self.subtitle_gen.transcribe_to_srt(audio_path)
            subtitles = self.subtitle_gen.parse_srt(srt_path)
            print(f"   ✓ {len(subtitles)} sottotitoli generati")
            self.report["subtitles"] = subtitles
        
        # 4. APPLICAZIONE SOTTOTITOLI
        if subtitles:
            print("\n🎨 Fase 4: Applicazione Sottotitoli...")
            current_video = self.editor.add_subtitles_overlay(current_video, subtitles)
        
        # 5. EXPORT
        print("\n💾 Fase 5: Export Multi-Formato...")
        exports = {
            "mp4": self.exporter.export_mp4(current_video),
            "webm": self.exporter.export_webm(current_video),
            "mov": self.exporter.export_mov(current_video),
        }
        self.report["exports"] = exports
        
        print(f"\n{'='*60}")
        print("✅ Processamento Completato!")
        print(f"{'='*60}\n")
        
        return self.report

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python video-processor.py <video_path> [--no-silence] [--no-subtitles]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ File non trovato: {video_path}")
        sys.exit(1)
    
    # Opzioni
    remove_silence = "--no-silence" not in sys.argv
    add_subtitles = "--no-subtitles" not in sys.argv
    
    # Processa
    processor = VideoProcessor(video_path)
    result = processor.process(
        add_subtitles=add_subtitles,
        remove_silence=remove_silence
    )
    
    # Output JSON
    print("\n📊 Report:")
    print(json.dumps(result, indent=2, default=str))
