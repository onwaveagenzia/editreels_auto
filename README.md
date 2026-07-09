# 🎬 ONWAVE Video Assistant Skill

**Skill specializzata per editing video professionale end-to-end con sottotitoli automatici, animazioni sincronizzate e voiceover sintetizzati.**

Creato per ONWAVE studio creativo - trasforma contenuti grezzi in video di qualità broadcast in minuti.

---

## ✨ Caratteristiche Principali

### 🎥 Video Processing
- **Analisi intelligente**: Rileva silenzi, qualità audio, problemi di sync
- **Auto-cutting**: Rimuove automaticamente parti morte e silenzi lunghi
- **Multi-format export**: MP4 (H.264), WebM (VP9), MOV (ProRes)
- **4K support**: Elabora fino a 4K, downsample automatico

### 📝 Subtitle Generation
- **Speech-to-text automatico**: Usa Whisper per trascrizioni accurate
- **Sincronizzazione perfetta**: Timing preciso al millisecondo
- **Formati multipli**: SRT, VTT, ASS
- **Styling personalizzato**: Font, colore, posizione configurabili

### 🎙️ Voice Synthesis (ElevenLabs)
- **4 profili vocali**: Professional, Warm, Energetic, Deep
- **Qualità cinema**: AI-driven text-to-speech di alta qualità
- **Sincronizzazione A/V**: Merge perfetto audio-video
- **Batch processing**: Processa multipli script in parallelo

### ✨ Animazioni Sincronizzate
- **15+ tipi di animazioni**: Zoom, pan, fade, slide, rotate, pulse, etc.
- **5 stili predefiniti**: Social Media, Educational, Corporate, Testimonial, Action
- **Keyword-based**: Animazioni automatiche su parole chiave
- **Hyperframes ready**: Esporta JSON compatibile Hyperframes

---

## 🚀 Quick Start

### 1. Setup Iniziale

```bash
# Clone la skill
cd /path/to/skills
git clone <skill-repo> onwave-video-assistant

# Installa dipendenze
cd onwave-video-assistant
pip install -r requirements.txt

# Configura API key
export ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY
```

### 2. Elabora un Video

```bash
# Workflow completo: analizza → taglia → sottotitoli → export
python scripts/video-processor.py input.mp4

# Con opzioni personalizzate
python scripts/video-processor.py input.mp4 --no-silence --no-subtitles
```

### 3. Aggiungi Voiceover

```bash
# Crea voiceover da script
python scripts/elevenlabs-sync.py input.mp4 \
  --text "Descrizione del video" \
  --voice professional \
  --output output.mp4
```

### 4. Genera Animazioni

```bash
# Auto-generate animazioni
python scripts/animations.py

# Output: animations.json (Hyperframes ready)
```

---

## 📋 File Structure

```
onwave-video-skill/
├── SKILL.md                          # Skill metadata & workflow
├── README.md                         # Questa documentazione
├── config.yaml                       # Configurazione centralizzata
├── requirements.txt                  # Dipendenze Python
│
├── scripts/
│   ├── video-processor.py           # Core video editing
│   ├── elevenlabs-sync.py           # ElevenLabs integration
│   ├── animations.py                # Animazioni Hyperframes
│   └── utils/
│       ├── ffmpeg_wrapper.py
│       ├── audio_analyzer.py
│       └── subtitle_formatter.py
│
├── references/
│   ├── elevenlabs-integration.md    # ElevenLabs API guide
│   ├── hyperframes-animations.md    # Animazioni guide
│   ├── voice-profiles.md            # Voice profiles dettagliati
│   └── troubleshooting.md           # Common issues & fixes
│
├── assets/
│   ├── subtitle-templates.json      # Preset stili sottotitoli
│   ├── animation-presets.json       # Animation templates
│   └── voice-samples/               # Audio di prova voiceover
│
└── examples/
    ├── social_media_workflow.md     # Caso d'uso: Social
    ├── corporate_video.md           # Caso d'uso: Corporate
    └── tutorial_video.md            # Caso d'uso: Educational
```

---

## 🎯 Uso per Caso d'Uso

### Caso 1: Content Social Media (TikTok/Reels)

```bash
python scripts/video-processor.py raw_footage.mp4

# Output: Verticale 1080x1920, sottotitoli bold, animazioni energiche
```

→ Vedi: `examples/social_media_workflow.md`

### Caso 2: Video Educativo/Tutorial

```bash
python scripts/video-processor.py screencast.mp4 \
  && python scripts/animations.py --style educational
```

→ Vedi: `examples/tutorial_video.md`

### Caso 3: Branding/Corporate Video

```bash
python scripts/elevenlabs-sync.py interview.mp4 \
  --script corporate_voiceover.txt \
  --voice professional
```

→ Vedi: `examples/corporate_video.md`

---

## 📊 API Reference

### VideoProcessor

```python
from scripts.video_processor import VideoProcessor

processor = VideoProcessor("input.mp4")
result = processor.process(
    add_subtitles=True,
    remove_silence=True
)

# Output
# {
#   "analysis": {...},
#   "subtitles": [...],
#   "exports": {
#     "mp4": "output_final.mp4",
#     "webm": "output_web.webm",
#     "mov": "output_pro.mov"
#   }
# }
```

### ElevenLabsClient

```python
from scripts.elevenlabs_sync import ElevenLabsClient, VoiceSettings

client = ElevenLabsClient(api_key)

# List voci disponibili
voices = client.list_voices()

# Genera audio
voice = VoiceSettings(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    stability=0.5,
    similarity_boost=0.75
)
client.text_to_speech("Testo", voice, "output.mp3")
```

### AnimationGenerator

```python
from scripts.animations import AnimationGenerator, HyperframesGenerator

# Generate da subtitle
animations = AnimationGenerator.from_transcript(
    subtitles,
    video_style="social_media",
    intensity=0.9
)

# Generate da keyword
animations = AnimationGenerator.from_keywords(
    text="...",
    subtitles=subtitles,
    keyword_animations={"importante": "highlight", "veloce": "zoom_in"}
)

# Export JSON
HyperframesGenerator.generate_json(animations, "animations.json")
```

---

## 🔧 Configurazione

Modifica `config.yaml` per personalizzare:

```yaml
# Qualità output
video:
  output_formats:
    mp4:
      bitrate_video: "8000k"  # Aumenta per qualità +
      bitrate_audio: "128k"

# Voce default
voices:
  default: "professional"  # Cambia profilo

# Animazioni
animations:
  default_style: "social_media"
  default_intensity: 0.8
```

---

## 🎨 Voice Profiles

### 1. **Professional** (Default)
```bash
--voice professional
```
- Tone: Neutrale, credibile
- Use: Corporate, presentazioni, formale
- Intensity: Media

### 2. **Warm**
```bash
--voice warm
```
- Tone: Amichevole, accogliente
- Use: Tutorial, storytelling, educational
- Intensity: Alta

### 3. **Energetic**
```bash
--voice energetic
```
- Tone: Dinamica, entusiasta
- Use: Social media, promo, call-to-action
- Intensity: Massima

### 4. **Deep**
```bash
--voice deep
```
- Tone: Autorevole, sofisticata
- Use: Narrazioni, documentari, branding
- Intensity: Media-bassa

---

## 📚 Documentazione Dettagliata

### Per ElevenLabs API
→ Leggi: `references/elevenlabs-integration.md`

### Per Animazioni Hyperframes
→ Leggi: `references/hyperframes-animations.md`

### Per Troubleshooting
→ Leggi: `references/troubleshooting.md`

### Per Esempi Pratici
→ Vedi: `examples/` directory

---

## 🐛 Troubleshooting

### Errore: "FFmpeg not found"
```bash
# Installa FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

### Errore: "ELEVENLABS_API_KEY not set"
```bash
export ELEVENLABS_API_KEY=sk_your_key_here
# Oppure modifica config.yaml
```

### Sottotitoli non sincronizzati
```bash
# Verifica audio
ffprobe -show_streams input.mp4

# Rigenera con engine diverso
python scripts/video-processor.py input.mp4 --stt-engine google_cloud
```

### Video Out of Sync
```bash
# Aggiungi delay audio
ffmpeg -i output.mp4 -itsoffset 0.5 -i output.mp3 -c:v copy -map 0:v:0 -map 1:a fixed.mp4
```

→ Più help: `references/troubleshooting.md`

---

## 🚄 Performance Tips

### 1. Abilita GPU
```bash
# In config.yaml
performance:
  enable_gpu_acceleration: true
```

### 2. Parallel Processing
```bash
# Processa multipli video in parallelo
for video in *.mp4; do
  python scripts/video-processor.py "$video" &
done
wait
```

### 3. Caching
```yaml
# Riusa file già elaborati
performance:
  enable_caching: true
  cache_ttl_hours: 72
```

### 4. Quality vs Speed
```yaml
performance:
  quality_preset: "fast"  # fast, medium, high
```

---

## 📊 Metriche & Monitoring

### Output Report
```json
{
  "analysis": {
    "duration_seconds": 120,
    "fps": 30,
    "resolution": "1920x1080",
    "silenzi_rilevati": 5,
    "potential_savings_seconds": 35.2
  },
  "subtitles": [
    {"start": 0, "end": 3, "text": "..."}
  ],
  "exports": {
    "mp4": "output_final.mp4",
    "webm": "output_web.webm",
    "mov": "output_pro.mov"
  }
}
```

### Logging
```bash
# Abilita debug logging
export LOG_LEVEL=DEBUG
python scripts/video-processor.py input.mp4
```

---

## 💡 Best Practices

### 1. Upload Video Qualitativo
- Minimo: 720p
- Consigliato: 1080p+
- Audio: Chiaro, volume consistente

### 2. Script Optimization (per voiceover)
```
✓ BUONO: "Il marketing digitale è..."
✗ MALE: "IlMarketingDigitaleÈ..."

✓ BUONO: Pause naturali con virgole
✗ MALE: Blocco di testo continuo
```

### 3. Timing Perfetto
```python
# Sincronizza animazioni con audio
for sub in subtitles:
    animation.start_time = sub["start"] + 0.1  # Piccolo delay
    animation.duration = sub["end"] - sub["start"] - 0.2
```

### 4. A/B Testing Voice
```bash
# Genera 4 versioni con voci diverse
for voice in professional warm energetic deep; do
  python scripts/elevenlabs-sync.py video.mp4 \
    --text "Script" --voice $voice \
    --output test_${voice}.mp4
done
```

---

## 🔐 Security & Best Practices

### API Key Management
```bash
# ✓ CORRETTO: Environment variable
export ELEVENLABS_API_KEY=sk_...

# ✗ SBAGLIATO: Hardcoded nel codice
API_KEY = "sk_..."  # NEVER!
```

### File Permissions
```bash
chmod 600 config.yaml  # Lettura solo per proprietario
chmod 755 scripts/     # Eseguibili
```

### Cleanup Automatico
```yaml
paths:
  auto_cleanup: true
  cleanup_after_hours: 24  # Rimuove temp files dopo 24h
```

---

## 📈 Roadmap

- [ ] Subtitle translation multi-lingua
- [ ] AI-powered cut suggestions (ML detection)
- [ ] Real-time preview durante processing
- [ ] Custom voice cloning da campione audio
- [ ] Batch API per processing in background
- [ ] Integration Google Drive/Dropbox
- [ ] Dashboard web di monitoraggio
- [ ] Export preset per piattaforme (YouTube, TikTok, etc)

---

## 🤝 Support & Contribute

### Report Bug
```bash
# Crea issue con dettagli
- Descrizione bug
- Comando esatto che fallisce
- Output/error message
- Video/file di test se possibile
```

### Contribuisci
```bash
# Branch → Test → PR
git checkout -b feature/miglioramento
python -m pytest tests/
git push origin feature/miglioramento
```

---

## 📄 License & Credits

Creato per **ONWAVE Studio Creativo**

ONWAVE è uno studio creativo specializzato in:
- 🎨 Branding & Identità
- 💻 Sviluppo Custom
- 🎥 Produzione Video & Contenuti
- 📱 UX/UI Design
- 🚀 Performance Marketing

**Website**: https://onwave.studio

---

## 📞 Contatti

- **Support**: support@onwave.studio
- **Sales**: sales@onwave.studio
- **Technical**: tech@onwave.studio

---

**Made with ❤️ by ONWAVE** | Transforming Ideas into High-Performance Digital Ecosystems
