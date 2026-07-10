#!/usr/bin/env python3
"""
ONWAVE Video Processor (self-contained, no external scripts/ dependency)
Rimozione silenzi + color grading + encoding preset social media.

Stessa logica validata manualmente su sandbox, ora portata dentro api/
così il container Railway (build scope = api/) la trova ed esegue da solo.
"""

import re
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

PRESETS = {
    "social_media": {
        "resolution": (1080, 1920),
        "bitrate": "7500k",
        "saturation": 1.20,
        "contrast": 1.10,
        "silence_db": -35.0,
        "silence_min_duration": 1.0,
    },
    "educational": {
        "resolution": (1920, 1080),
        "bitrate": "5000k",
        "saturation": 1.05,
        "contrast": 1.05,
        "silence_db": -40.0,
        "silence_min_duration": 2.0,
    },
    "corporate": {
        "resolution": (1440, 2560),
        "bitrate": "6000k",
        "saturation": 1.0,
        "contrast": 1.05,
        "silence_db": -40.0,
        "silence_min_duration": 2.0,
    },
    "testimonial": {
        "resolution": (1280, 720),
        "bitrate": "4000k",
        "saturation": 1.0,
        "contrast": 1.0,
        "silence_db": -40.0,
        "silence_min_duration": 2.5,
    },
}


# ============================================================================
# SILENCE DETECTION
# ============================================================================

def detect_silences(video_path: str, db_threshold: float, min_duration: float) -> List[Tuple[float, float]]:
    """Rileva i silenzi nel video usando ffmpeg silencedetect"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={db_threshold}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    log = result.stderr

    starts = [float(x) for x in re.findall(r'silence_start:\s*([\d.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end:\s*([\d.]+)', log)]

    return list(zip(starts, ends))


def get_video_duration(video_path: str) -> float:
    """Ottiene la durata del video in secondi"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])


def compute_keep_segments(
    silences: List[Tuple[float, float]],
    duration: float,
    pad: float = 0.15,
    min_segment: float = 0.3
) -> List[Tuple[float, float]]:
    """Calcola i segmenti da TENERE escludendo i silenzi rilevati"""
    keep = []
    cursor = 0.0

    for s, e in silences:
        seg_start = cursor
        seg_end = max(cursor, s + pad)
        if seg_end - seg_start > 0.05:
            keep.append((seg_start, seg_end))
        cursor = max(cursor, e - pad)

    if cursor < duration:
        keep.append((cursor, duration))

    return [(s, e) for s, e in keep if e - s >= min_segment]


# ============================================================================
# BATCH PROCESSING (per evitare timeout su video lunghi)
# ============================================================================

def group_into_batches(segments: List[Tuple[float, float]], max_batch_duration: float = 45.0) -> List[List[Tuple[float, float]]]:
    """Raggruppa i segmenti in batch per processing incrementale"""
    batches = []
    current = []
    current_dur = 0.0

    for s, e in segments:
        dur = e - s
        if current and current_dur + dur > max_batch_duration:
            batches.append(current)
            current = []
            current_dur = 0.0
        current.append((s, e))
        current_dur += dur

    if current:
        batches.append(current)

    return batches


def build_batch_filter(segments: List[Tuple[float, float]], saturation: float, contrast: float) -> str:
    """Costruisce il filter_complex FFmpeg per un batch di segmenti"""
    parts = []
    vlabels = ""
    alabels = ""

    for j, (s, e) in enumerate(segments):
        parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{j}];")
        parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{j}];")
        vlabels += f"[v{j}]"
        alabels += f"[a{j}]"

    n = len(segments)
    parts.append(f"{vlabels}concat=n={n}:v=1:a=0[vc];")
    parts.append(f"{alabels}concat=n={n}:v=0:a=1[ac];")
    parts.append(f"[vc]eq=saturation={saturation}:contrast={contrast}[vout];[ac]anull[aout]")

    return "".join(parts)


def encode_batch(input_video: str, segments: List[Tuple[float, float]],
                  output_path: str, preset: Dict, use_scale: bool = False) -> None:
    """Elabora un singolo batch: taglio + color grading + encoding"""
    filt = build_batch_filter(segments, preset["saturation"], preset["contrast"])

    # Aggiunge scale solo se necessario (evita upscale inutile su risoluzioni già corrette)
    if use_scale:
        w, h = preset["resolution"]
        filt = filt.replace("[vout];", f"[vscaled];[vscaled]scale={w}:{h}[vout];")

    cmd = [
        "ffmpeg", "-y", "-i", input_video,
        "-filter_complex", filt,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", preset["bitrate"], "-maxrate", preset["bitrate"], "-bufsize", "15000k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-r", "30",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg batch encode fallito: {result.stderr[-500:]}")


def concat_batches(batch_paths: List[str], output_path: str) -> None:
    """Unisce i batch elaborati (stream copy, velocissimo)"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for p in batch_paths:
            f.write(f"file '{p}'\n")
        concat_list = f.name

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    Path(concat_list).unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat fallito: {result.stderr[-500:]}")


# ============================================================================
# PIPELINE COMPLETA
# ============================================================================

def process_video(
    input_path: str,
    output_path: str,
    preset_name: str = "social_media",
    remove_silence: bool = True
) -> Dict:
    """
    Pipeline completa: rileva silenzi -> taglia -> color grading -> encode.

    Returns: dict con statistiche (durata originale, finale, silenzi rimossi)
    """
    if preset_name not in PRESETS:
        raise ValueError(f"Preset sconosciuto: {preset_name}. Disponibili: {list(PRESETS.keys())}")

    preset = PRESETS[preset_name]
    original_duration = get_video_duration(input_path)

    if remove_silence:
        silences = detect_silences(
            input_path,
            preset["silence_db"],
            preset["silence_min_duration"]
        )
        segments = compute_keep_segments(silences, original_duration)
    else:
        segments = [(0.0, original_duration)]

    if not segments:
        segments = [(0.0, original_duration)]

    final_duration = sum(e - s for s, e in segments)
    batches = group_into_batches(segments)

    logger.info(f"📊 {len(silences) if remove_silence else 0} silenzi rilevati, "
                f"{len(segments)} segmenti, {len(batches)} batch")

    work_dir = tempfile.mkdtemp(prefix="onwave_process_")
    batch_paths = []

    try:
        for i, batch in enumerate(batches):
            batch_output = str(Path(work_dir) / f"batch_{i}.mp4")
            encode_batch(input_path, batch, batch_output, preset)
            batch_paths.append(batch_output)
            logger.info(f"✓ Batch {i+1}/{len(batches)} completato")

        if len(batch_paths) == 1:
            Path(batch_paths[0]).rename(output_path)
        else:
            concat_batches(batch_paths, output_path)

    finally:
        for p in batch_paths:
            Path(p).unlink(missing_ok=True)
        try:
            Path(work_dir).rmdir()
        except OSError:
            pass

    return {
        "preset": preset_name,
        "original_duration_seconds": round(original_duration, 1),
        "final_duration_seconds": round(final_duration, 1),
        "silence_removed_seconds": round(original_duration - final_duration, 1),
        "num_segments": len(segments),
        "output_path": output_path
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Uso: python video_processor.py input.mp4 output.mp4 [preset]")
        sys.exit(1)

    preset = sys.argv[3] if len(sys.argv) > 3 else "social_media"
    result = process_video(sys.argv[1], sys.argv[2], preset_name=preset)
    print(json.dumps(result, indent=2))
