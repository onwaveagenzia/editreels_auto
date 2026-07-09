# ElevenLabs API Integration Guide

Guida completa per integrare voci sintetizzate di qualità cinema nel workflow ONWAVE.

## 📋 Indice

1. [Configurazione](#configurazione)
2. [Voice Profiles](#voice-profiles)
3. [API Endpoints](#api-endpoints)
4. [Advanced Features](#advanced-features)
5. [Best Practices](#best-practices)

---

## Configurazione

### 1. API Key Setup

```bash
export ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY
```

### 2. Verifica Connessione

```bash
python scripts/elevenlabs-sync.py --list-voices
```

Questo elenca tutte le voci disponibili sul tuo account.

---

## Voice Profiles

ONWAVE include 4 profili vocali ottimizzati:

### 1. **Professional** (Default)
- **Voice**: Bella (Female, Neutral)
- **Stability**: 0.5
- **Similarity**: 0.75
- **Use Case**: Video corporate, presentazioni, content formale
- **Tone**: Neutrale, professionale, credibile

```bash
python scripts/elevenlabs-sync.py video.mp4 --text "Testo" --voice professional
```

### 2. **Warm**
- **Voice**: Duane (Male, Warm)
- **Stability**: 0.4
- **Similarity**: 0.85
- **Use Case**: Tutorial, educational, storytelling
- **Tone**: Accogliente, amichevole, coinvolgente

```bash
python scripts/elevenlabs-sync.py video.mp4 --text "Testo" --voice warm
```

### 3. **Energetic**
- **Voice**: Andrea (Female, Dynamic)
- **Stability**: 0.6
- **Similarity**: 0.8
- **Use Case**: Social media, promo, content veloce
- **Tone**: Energica, dinamica, entusiasta

```bash
python scripts/elevenlabs-sync.py video.mp4 --text "Testo" --voice energetic
```

### 4. **Deep**
- **Voice**: Adam (Male, Deep)
- **Stability**: 0.7
- **Similarity**: 0.7
- **Use Case**: Narrazioni, documentari, branding
- **Tone**: Profonda, autorevole, sofisticata

```bash
python scripts/elevenlabs-sync.py video.mp4 --text "Testo" --voice deep
```

---

## API Endpoints

### Text-to-Speech (TTS)

**Endpoint**: `POST /v1/text-to-speech/{voice_id}`

**Payload**:
```json
{
  "text": "Your text here",
  "model_id": "eleven_monolingual_v1",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}
```

**Parametri**:
- `text` (string, max 1000 char): Testo da sintetizzare
- `model_id` (string): Modello vocale (default: `eleven_monolingual_v1`)
- `stability` (float, 0-1): Quanto coerente è la voce
  - **Basso (0.0-0.3)**: Variabilità naturale, più espressivo
  - **Medio (0.4-0.6)**: Bilancia coerenza ed espressione (CONSIGLIATO)
  - **Alto (0.7-1.0)**: Molto coerente, meno variazioni
- `similarity_boost` (float, 0-1): Fedeltà al voice clone
  - **Basso (0.3-0.5)**: Meno simile, più naturale
  - **Medio (0.6-0.8)**: Buon equilibrio (CONSIGLIATO)
  - **Alto (0.9-1.0)**: Massima somiglianza al clone

**Response**:
```
Audio MP3/WAV binary data
```

### Get User Info

**Endpoint**: `GET /v1/user`

Verifica crediti disponibili e statistiche di uso.

```bash
curl -H "xi-api-key: YOUR_KEY" https://api.elevenlabs.io/v1/user
```

---

## Advanced Features

### 1. Custom Voice Clones

Se hai creato un voice clone personalizzato:

```python
from scripts.elevenlabs_sync import ElevenLabsClient, VoiceSettings

client = ElevenLabsClient(api_key="sk_...")
custom_voice = VoiceSettings(
    voice_id="your_cloned_voice_id",
    stability=0.6,
    similarity_boost=0.85
)

client.text_to_speech("Testo", custom_voice, "output.mp3")
```

### 2. Batch Processing

Processa multipli script con voce diversa:

```bash
for script in scripts/*.txt; do
  python scripts/elevenlabs-sync.py video.mp4 \
    --script "$script" \
    --voice warm \
    --output "$(basename $script .txt).mp4"
done
```

### 3. Language Support

ElevenLabs supporta più lingue. Per italiano, usa `eleven_monolingual_v1`:

```python
voice_settings = VoiceSettings(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    stability=0.5,
    similarity_boost=0.75,
    model_id="eleven_monolingual_v1"  # Monolingual per miglior qualità
)
```

### 4. Audio Mixing

Mescola voiceover con audio originale:

```bash
python scripts/elevenlabs-sync.py video.mp4 \
  --text "Voiceover" \
  --voice professional \
  --keep-original  # Mescola invece di sostituire
```

---

## Best Practices

### 1. Script Optimization

- **Lunghezza**: Mantieni paragrafi sotto 500 caratteri
- **Punteggiatura**: Usa virgole, punti per pause naturali
- **Pronunciation**: Per parole difficili, usa descrizioni fonetiche

```
✓ BUONO: "Il marketing digitale, o digital marketing, è l'insieme di strategie..."
✗ MALE: "IlMarketingDigitalEcheDireMarketingÈLInsiemediBianceStrategic..."
```

### 2. Stabilità e Similarità

**Profilo Consigliato per Tipi di Contenuto**:

| Tipo Contenuto | Stability | Similarity | Profilo |
|---|---|---|---|
| Corporate Video | 0.5-0.6 | 0.7-0.8 | Professional |
| Tutorial | 0.4-0.5 | 0.8-0.85 | Warm |
| Social Media Promo | 0.6-0.7 | 0.75-0.8 | Energetic |
| Audiobook/Narration | 0.7-0.8 | 0.7-0.75 | Deep |

### 3. Cost Optimization

- **Crediti per Character**: Tipicamente 1 credito per char
- **Batch Processing**: Sintetizza una volta, riusa il file
- **Caching**: Salva audio generati per futuri utilizzi

```bash
# Hash testo per cache
HASH=$(echo -n "$TEXT" | md5sum | cut -d' ' -f1)
CACHE_FILE="cache/audio_${HASH}.mp3"

if [ ! -f "$CACHE_FILE" ]; then
  python scripts/elevenlabs-sync.py ... > "$CACHE_FILE"
fi
```

### 4. Quality Assurance

Verifica prima di esportare:

1. **Pronuncia**: Ascolta per errori di pronuncia
2. **Timing**: Sincronizzazione audio-video perfetta
3. **Tono**: Coerente con brand voice
4. **Livello Audio**: Normalizzato a -23 LUFS (broadcast standard)

```bash
# Normalizza audio con FFmpeg
ffmpeg -i voiceover.mp3 -af "loudnorm=I=-23:TP=-1.5:LRA=11" output.mp3
```

### 5. A/B Testing

Prova multipli profili per trovare il migliore:

```bash
for voice in professional warm energetic deep; do
  python scripts/elevenlabs-sync.py video.mp4 \
    --text "Sample text" \
    --voice $voice \
    --output "test_${voice}.mp4"
done
```

Poi mostra i campioni al client per feedback.

---

## Troubleshooting

### Errore: "Insufficient Credits"
- Verifica limite crediti: `python scripts/elevenlabs-sync.py --list-voices`
- Upgrade piano su https://elevenlabs.io/billing

### Errore: "Invalid API Key"
- Verifica key: `echo $ELEVENLABS_API_KEY`
- Rigenera key su https://elevenlabs.io/account

### Audio Out of Sync
- Aggiungi delay: `ffmpeg -itsoffset 0.5 -i voiceover.mp3 ...`
- Verifica FPS video matches FFmpeg settings

### Pronunciation Issues
- Usa spelled-out phonetics in script
- Per parole tecniche, crea custom voice clone
- Riprova con profilo diverso (warm vs professional)

---

## Script Template

```python
from scripts.elevenlabs_sync import VoiceoverProcessor

processor = VoiceoverProcessor(api_key="sk_...")

result = processor.process_script(
    video_path="input.mp4",
    script_text="Testo dello script",
    voice_profile="professional",
    output_dir="./output",
    keep_original_audio=False
)

print(f"✓ Video completato: {result['video_path']}")
```

---

**API Reference**: https://elevenlabs.io/docs/api-reference
**Pricing**: https://elevenlabs.io/pricing
**Status**: https://status.elevenlabs.io/
