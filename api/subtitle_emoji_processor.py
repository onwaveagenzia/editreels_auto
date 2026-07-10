#!/usr/bin/env python3
"""
ONWAVE Subtitle & Emoji Processor
Trascrizione automatica (faster-whisper) + burn-in sottotitoli + overlay emoji
contestuali basate su parole chiave rilevate nel parlato.

Questo modulo gira SOLO su un ambiente con accesso internet libero
(Railway/Render), perché deve scaricare il modello Whisper al primo utilizzo.
"""

import os
import re
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# TRASCRIZIONE (faster-whisper)
# ============================================================================

@dataclass
class Segment:
    start: float
    end: float
    text: str

_MODEL_CACHE = {}

def _get_model(model_size: str = "small"):
    """Carica (o riusa dalla cache) il modello Whisper"""
    from faster_whisper import WhisperModel

    if model_size not in _MODEL_CACHE:
        logger.info(f"Caricamento modello Whisper '{model_size}'...")
        _MODEL_CACHE[model_size] = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"  # più leggero, ottimo per CPU-only
        )
    return _MODEL_CACHE[model_size]


def transcribe_video(video_path: str, model_size: str = "small",
                      language: Optional[str] = "it") -> List[Segment]:
    """
    Trascrive l'audio del video e restituisce segmenti con timestamp.

    Args:
        video_path: percorso del video
        model_size: tiny, base, small, medium, large-v3 (più grande = più preciso e più lento)
        language: codice lingua (es. 'it', 'en') o None per auto-detect
    """
    model = _get_model(model_size)

    segments_iter, info = model.transcribe(
        video_path,
        language=language,
        vad_filter=True,  # filtra automaticamente i silenzi
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    segments = [
        Segment(start=s.start, end=s.end, text=s.text.strip())
        for s in segments_iter
    ]

    logger.info(f"Trascrizione completata: {len(segments)} segmenti, lingua: {info.language}")
    return segments


# ============================================================================
# GENERAZIONE SOTTOTITOLI (.srt)
# ============================================================================

def _format_srt_time(seconds: float) -> str:
    """Converte secondi in formato SRT: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: List[Segment], max_chars_per_line: int = 35) -> str:
    """Genera contenuto file .srt dai segmenti trascritti"""
    lines = []
    for i, seg in enumerate(segments, 1):
        text = seg.text
        # Spezza in due righe se troppo lungo
        if len(text) > max_chars_per_line:
            words = text.split()
            mid = len(words) // 2
            text = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

        lines.append(str(i))
        lines.append(f"{_format_srt_time(seg.start)} --> {_format_srt_time(seg.end)}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def save_srt(segments: List[Segment], output_path: str):
    """Salva i sottotitoli su file .srt"""
    content = generate_srt(segments)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"✓ Sottotitoli salvati: {output_path}")


# ============================================================================
# RILEVAMENTO EMOJI DA PAROLE CHIAVE
# ============================================================================

# Mappa parole chiave (italiano + inglese) -> emoji
# Espandibile liberamente
EMOJI_KEYWORDS = {
    # Entusiasmo / energia
    "incredibile": "🤯", "pazzesco": "🤯", "wow": "😲", "assurdo": "🤯",
    "fantastico": "🔥", "fenomenale": "🔥", "top": "🔥", "grande": "💪",
    "amazing": "🤯", "wow": "😲", "insane": "🤯", "crazy": "🤯",

    # Amore / positività
    "amore": "❤️", "adoro": "😍", "bellissimo": "😍", "love": "❤️",

    # Soldi / business
    "soldi": "💰", "guadagno": "💰", "vendite": "📈", "fatturato": "💰",
    "crescita": "📈", "successo": "🏆", "money": "💰", "profit": "📈",

    # Attenzione / urgenza
    "attenzione": "⚠️", "importante": "❗", "occhio": "👀", "guarda": "👀",
    "warning": "⚠️", "attention": "❗",

    # Risate / ironia
    "ridere": "😂", "divertente": "😂", "scherzo": "😂", "lol": "😂",
    "funny": "😂", "haha": "😂",

    # Domande / riflessione
    "domanda": "🤔", "pensare": "🤔", "perché": "🤔", "curioso": "🧐",

    # Tempo / velocità
    "veloce": "⚡", "subito": "⚡", "adesso": "⏰", "tempo": "⏰",
    "fast": "⚡", "now": "⏰",

    # Conferma / approvazione
    "sì": "✅", "esatto": "✅", "perfetto": "✅", "ok": "👍",
    "yes": "✅", "perfect": "✅",

    # Rifiuto / negazione
    "no": "❌", "mai": "❌", "sbagliato": "❌", "never": "❌",

    # Idee / creatività
    "idea": "💡", "creativo": "🎨", "innovazione": "💡", "idea": "💡",

    # Crescita / obiettivi
    "obiettivo": "🎯", "traguardo": "🏆", "risultato": "🎯", "goal": "🎯",
}

# Ordina per lunghezza decrescente per evitare match parziali errati
_SORTED_KEYWORDS = sorted(EMOJI_KEYWORDS.keys(), key=len, reverse=True)


@dataclass
class EmojiCue:
    time: float
    emoji: str
    trigger_word: str


def detect_emoji_cues(segments: List[Segment], max_per_segment: int = 1) -> List[EmojiCue]:
    """
    Analizza i segmenti trascritti e individua dove inserire emoji
    in base alle parole chiave rilevate.
    """
    cues = []

    for seg in segments:
        text_lower = seg.text.lower()
        found_in_segment = 0

        for keyword in _SORTED_KEYWORDS:
            if found_in_segment >= max_per_segment:
                break

            # Match come parola intera (evita match dentro altre parole)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, text_lower)

            if match:
                # Posiziona l'emoji proporzionalmente al punto della parola nel segmento
                word_position_ratio = match.start() / max(len(text_lower), 1)
                cue_time = seg.start + (seg.end - seg.start) * word_position_ratio

                cues.append(EmojiCue(
                    time=cue_time,
                    emoji=EMOJI_KEYWORDS[keyword],
                    trigger_word=keyword
                ))
                found_in_segment += 1

    logger.info(f"✓ Rilevate {len(cues)} emoji cue dal contenuto parlato")
    return cues


# ============================================================================
# RENDER EMOJI COME PNG (per overlay FFmpeg)
# ============================================================================

def render_emoji_png(emoji_char: str, output_path: str, size: int = 160) -> bool:
    """
    Renderizza un singolo emoji come immagine PNG trasparente,
    usando il font Noto Color Emoji (deve essere installato nel sistema).
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    ]

    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                # Noto Color Emoji ha una dimensione fissa nativa (109px), scaliamo dopo
                font = ImageFont.truetype(fp, 109)
                break
            except Exception as e:
                logger.warning(f"Font {fp} non caricabile: {e}")

    if font is None:
        logger.error("❌ Font emoji non trovato. Installa 'fonts-noto-color-emoji'.")
        return False

    try:
        draw.text((size // 2, size // 2), emoji_char, font=font,
                   embedded_color=True, anchor="mm")
    except TypeError:
        # Fallback per versioni Pillow senza supporto embedded_color/anchor
        draw.text((10, 10), emoji_char, font=font)

    img.save(output_path)
    return True


def prepare_emoji_assets(cues: List[EmojiCue], work_dir: str) -> dict:
    """
    Genera un PNG per ogni emoji UNICA usata (non uno per ogni cue,
    per efficienza), restituendo mappa emoji -> percorso file.
    """
    unique_emojis = set(cue.emoji for cue in cues)
    emoji_files = {}

    for emoji_char in unique_emojis:
        safe_name = f"emoji_{abs(hash(emoji_char))}.png"
        output_path = os.path.join(work_dir, safe_name)

        if render_emoji_png(emoji_char, output_path):
            emoji_files[emoji_char] = output_path
        else:
            logger.warning(f"Skip emoji '{emoji_char}': render fallito")

    return emoji_files


# ============================================================================
# COSTRUZIONE COMANDO FFMPEG: SOTTOTITOLI + EMOJI OVERLAY
# ============================================================================

def build_ffmpeg_command(
    input_video: str,
    output_video: str,
    srt_path: Optional[str],
    emoji_cues: List[EmojiCue],
    emoji_files: dict,
    emoji_duration: float = 1.2,
    subtitle_style: Optional[str] = None
) -> List[str]:
    """
    Costruisce il comando FFmpeg completo che:
    1. Brucia i sottotitoli (se presenti)
    2. Sovrappone le emoji nei momenti giusti (se presenti)
    """

    if subtitle_style is None:
        subtitle_style = (
            "FontName=Arial,FontSize=14,PrimaryColour=&HFFFFFF,"
            "OutlineColour=&H000000,BorderStyle=3,Outline=2,"
            "Alignment=2,MarginV=60"
        )

    inputs = ["-i", input_video]
    filter_chain = []
    last_video_label = "0:v"

    # STEP 1: Sottotitoli
    if srt_path:
        escaped_srt = srt_path.replace(":", "\\:").replace("'", "\\'")
        filter_chain.append(
            f"[{last_video_label}]subtitles='{escaped_srt}':"
            f"force_style='{subtitle_style}'[vsub]"
        )
        last_video_label = "vsub"

    # STEP 2: Overlay emoji (ogni emoji unica è un input separato)
    emoji_input_index = {}
    for i, (emoji_char, path) in enumerate(emoji_files.items(), start=1):
        inputs += ["-i", path]
        emoji_input_index[emoji_char] = i

    for idx, cue in enumerate(emoji_cues):
        if cue.emoji not in emoji_input_index:
            continue
        input_idx = emoji_input_index[cue.emoji]
        start = cue.time
        end = cue.time + emoji_duration
        out_label = f"vov{idx}"

        # Piccolo effetto "pop": scala da 0 a 100% nei primi 0.15s
        filter_chain.append(
            f"[{input_idx}:v]scale=140:140[emj{idx}];"
            f"[{last_video_label}][emj{idx}]overlay="
            f"x=W-w-40:y=80:"
            f"enable='between(t,{start:.2f},{end:.2f})'[{out_label}]"
        )
        last_video_label = out_label

    filter_complex = ";".join(filter_chain) if filter_chain else None

    cmd = ["ffmpeg", "-y"] + inputs

    if filter_complex:
        cmd += ["-filter_complex", filter_complex, "-map", f"[{last_video_label}]", "-map", "0:a"]
    else:
        cmd += ["-map", "0:v", "-map", "0:a"]

    cmd += [
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_video
    ]

    return cmd


# ============================================================================
# PIPELINE COMPLETA
# ============================================================================

def add_subtitles_and_emojis(
    input_video: str,
    output_video: str,
    model_size: str = "small",
    language: Optional[str] = "it",
    burn_subtitles: bool = True,
    add_emojis: bool = True,
    save_srt_alongside: bool = True
) -> dict:
    """
    Pipeline completa: trascrizione -> sottotitoli -> emoji -> video finale.

    Returns:
        dict con: srt_path, num_segments, num_emoji_cues, output_video
    """
    logger.info(f"🎙️  Avvio trascrizione: {input_video}")
    segments = transcribe_video(input_video, model_size=model_size, language=language)

    if not segments:
        logger.warning("⚠️  Nessun segmento trascritto (audio vuoto o non rilevato)")

    srt_path = None
    if burn_subtitles and segments:
        srt_path = str(Path(output_video).with_suffix('.srt'))
        save_srt(segments, srt_path)

    emoji_cues = []
    emoji_files = {}
    if add_emojis and segments:
        emoji_cues = detect_emoji_cues(segments)
        if emoji_cues:
            work_dir = tempfile.mkdtemp(prefix="onwave_emoji_")
            emoji_files = prepare_emoji_assets(emoji_cues, work_dir)

    cmd = build_ffmpeg_command(
        input_video=input_video,
        output_video=output_video,
        srt_path=srt_path if burn_subtitles else None,
        emoji_cues=emoji_cues,
        emoji_files=emoji_files
    )

    logger.info(f"⚙️  Esecuzione FFmpeg ({len(emoji_files)} emoji uniche, "
                f"{len(emoji_cues)} cue totali)...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"❌ FFmpeg fallito: {result.stderr[-2000:]}")
        raise RuntimeError(f"FFmpeg processing failed: {result.stderr[-500:]}")

    logger.info(f"✓ Video finale generato: {output_video}")

    if not save_srt_alongside and srt_path and os.path.exists(srt_path):
        os.remove(srt_path)
        srt_path = None

    return {
        "output_video": output_video,
        "srt_path": srt_path,
        "num_segments": len(segments),
        "num_emoji_cues": len(emoji_cues),
        "transcript_preview": " ".join(s.text for s in segments[:5])
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Uso: python subtitle_emoji_processor.py input.mp4 output.mp4")
        sys.exit(1)

    result = add_subtitles_and_emojis(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))
