#!/usr/bin/env python3
"""
ONWAVE Video Quick Analysis - usando solo FFmpeg
Analisi rapida senza dipendenze pesanti
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import timedelta

def analyze_video(video_path: str) -> dict:
    """Analizza video usando ffprobe"""
    
    if not os.path.exists(video_path):
        return {"error": f"File non trovato: {video_path}"}
    
    # Get basic info
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-of", "json", video_path
    ]
    
    try:
        result = subprocess.run(cmd_probe, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
    except Exception as e:
        return {"error": f"Errore ffprobe: {e}"}
    
    # Extract video stream info
    video_stream = None
    audio_stream = None
    
    for stream in data.get('streams', []):
        if stream['codec_type'] == 'video':
            video_stream = stream
        elif stream['codec_type'] == 'audio':
            audio_stream = stream
    
    if not video_stream:
        return {"error": "Nessun stream video trovato"}
    
    # Calcola statistiche
    duration = float(video_stream.get('duration', 0))
    
    analysis = {
        "file": Path(video_path).name,
        "file_size_mb": os.path.getsize(video_path) / (1024 * 1024),
        "duration_seconds": duration,
        "duration_formatted": str(timedelta(seconds=int(duration))),
        "fps": eval(video_stream['r_frame_rate']),
        "resolution": f"{video_stream['width']}x{video_stream['height']}",
        "resolution_vertical": True if video_stream['height'] > video_stream['width'] else False,
        "codec_video": video_stream['codec_name'],
        "bit_rate_mbps": float(video_stream.get('bit_rate', 0)) / 1_000_000,
        "pixel_format": video_stream.get('pix_fmt', 'unknown'),
        "color_space": video_stream.get('color_space', 'unknown'),
    }
    
    if audio_stream:
        analysis['audio'] = {
            "codec": audio_stream['codec_name'],
            "sample_rate_hz": int(audio_stream['sample_rate']),
            "channels": audio_stream['channels'],
            "channel_layout": audio_stream.get('channel_layout', 'unknown'),
            "bit_rate_kbps": int(audio_stream.get('bit_rate', 0)) / 1000,
            "duration_seconds": float(audio_stream.get('duration', 0))
        }
    
    return analysis

def extract_audio(video_path: str, output_audio: str) -> bool:
    """Estrae audio in WAV"""
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-q:a", "9", "-n",
            "-vn",  # No video
            output_audio
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        print(f"Errore estrazione audio: {e}")
        return False

def detect_silences_simple(video_path: str) -> list:
    """Rileva silenzi usando ffmpeg silencedetect"""
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-af", "silencedetect=n=-40dB:d=2",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        silences = []
        stderr = result.stderr
        
        # Parse silencedetect output
        import re
        for line in stderr.split('\n'):
            if 'silence_start' in line or 'silence_end' in line:
                silences.append(line.strip())
        
        return silences
    except Exception as e:
        print(f"Errore detection silenzi: {e}")
        return []

def main():
    video_path = "/mnt/user-data/uploads/Video_1.mov"
    
    print("\n" + "="*70)
    print("🎬 ONWAVE Video Analysis - Test Case")
    print("="*70 + "\n")
    
    # Analisi
    print("📊 Fase 1: Analisi Video...\n")
    analysis = analyze_video(video_path)
    
    if "error" in analysis:
        print(f"❌ {analysis['error']}")
        return
    
    print(f"✓ File: {analysis['file']}")
    print(f"✓ Dimensione: {analysis['file_size_mb']:.1f} MB")
    print(f"✓ Durata: {analysis['duration_formatted']} ({analysis['duration_seconds']:.1f}s)")
    print(f"✓ Risoluzione: {analysis['resolution']} {'(VERTICAL)' if analysis['resolution_vertical'] else '(HORIZONTAL)'}")
    print(f"✓ FPS: {analysis['fps']}")
    print(f"✓ Video Codec: {analysis['codec_video']}")
    print(f"✓ Bitrate Video: {analysis['bit_rate_mbps']:.1f} Mbps")
    print(f"✓ Pixel Format: {analysis['pixel_format']}")
    print(f"✓ Color Space: {analysis['color_space']}")
    
    if 'audio' in analysis:
        audio = analysis['audio']
        print(f"\n🔊 Audio:")
        print(f"  ✓ Codec: {audio['codec']}")
        print(f"  ✓ Sample Rate: {audio['sample_rate_hz']} Hz")
        print(f"  ✓ Channels: {audio['channels']} ({audio['channel_layout']})")
        print(f"  ✓ Bitrate: {audio['bit_rate_kbps']:.1f} kbps")
    
    # Silence Detection
    print(f"\n⏭️  Fase 2: Rilevamento Silenzi...\n")
    print("🔍 Scanning per silenze lunghi (threshold: -40dB, durata: 2s)...")
    silences = detect_silences_simple(video_path)
    
    if silences:
        print(f"\n⚠️  Silenzi Rilevati ({len([s for s in silences if 'silence_start' in s])}): \n")
        for silence in silences[-10:]:  # Ultimi 10
            print(f"   {silence}")
    else:
        print("\n✓ Nessun silenzio lungo rilevato")
    
    # Recommendations
    print(f"\n💡 Fase 3: Raccomandazioni\n")
    
    recommendations = []
    
    # Risoluzione
    w, h = map(int, analysis['resolution'].split('x'))
    if w > 2160 or h > 2160:
        recommendations.append(f"⚠️  Risoluzione alta ({analysis['resolution']}): Considera downscale a 1080p per web")
    else:
        recommendations.append(f"✓ Risoluzione ottimale ({analysis['resolution']}) per broadcast")
    
    # Formato verticale
    if analysis['resolution_vertical']:
        recommendations.append(f"✓ Video VERTICALE perfetto per social media (TikTok, Reels, Shorts)")
    
    # Bitrate
    if analysis['bit_rate_mbps'] > 15:
        recommendations.append(f"⚠️  Bitrate alto ({analysis['bit_rate_mbps']:.1f} Mbps): Compressione consigliata per web")
    else:
        recommendations.append(f"✓ Bitrate ragionevole ({analysis['bit_rate_mbps']:.1f} Mbps)")
    
    # Audio
    if 'audio' in analysis:
        if analysis['audio']['sample_rate_hz'] != 48000:
            recommendations.append(f"ℹ️  Sample rate audio: {analysis['audio']['sample_rate_hz']} Hz (standard broadcast: 48kHz)")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    # Export Recommendations
    print(f"\n🎯 Fase 4: Strategie Export\n")
    
    export_rec = {
        "social_media": {
            "format": "MP4",
            "resolution": "1080x1920 (keep vertical)",
            "bitrate": "6-8 Mbps",
            "fps": 30,
            "note": "Ottimale per TikTok, Instagram Reels, YouTube Shorts"
        },
        "web": {
            "format": "WebM",
            "resolution": "Mantenere aspetto ratio",
            "bitrate": "4-6 Mbps",
            "fps": 30,
            "note": "Streaming leggero"
        },
        "archival": {
            "format": "MOV (ProRes)",
            "resolution": "Mantenere originale",
            "bitrate": "Lossless",
            "fps": 30,
            "note": "Per post-production"
        }
    }
    
    for format_type, specs in export_rec.items():
        print(f"  📁 {format_type.upper()}")
        for key, val in specs.items():
            print(f"     • {key}: {val}")
        print()
    
    # Final Report
    print("="*70)
    print("📋 REPORT COMPLETO JSON")
    print("="*70 + "\n")
    
    full_report = {
        "analysis": analysis,
        "silences": len([s for s in silences if 'silence_start' in s]),
        "recommendations": recommendations,
        "export_presets": export_rec,
        "next_steps": [
            "1. Esegui taglio silenzi: python scripts/video-processor.py",
            "2. Genera sottotitoli: speech-to-text automatico",
            "3. Applica animazioni: python scripts/animations.py",
            "4. Crea voiceover: python scripts/elevenlabs-sync.py",
            "5. Export multi-formato: MP4 + WebM + MOV"
        ]
    }
    
    print(json.dumps(full_report, indent=2, default=str))
    
    print("\n" + "="*70)
    print("✅ Analisi Completata!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
