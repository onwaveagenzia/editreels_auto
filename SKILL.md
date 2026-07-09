---
name: onwave-video-assistant
description: |
  Skill specializzata per ONWAVE per l'editing video professionale end-to-end. 
  Analizza video grezzi, estrae automaticamente trascrizioni, identifica e rimuove parti morte/errori, 
  applica animazioni dinamiche sincronizzate al contenuto, genera sottotitoli con timing perfetto, 
  e esporta in multipli formati (MP4, WebM, MOV). Usa ElevenLabs API per audio di qualità cinema 
  e Hyperframes per animazioni visually stunning. 
  
  Trigger quando l'utente: 
  - Carica video grezzi e vuole editarli professionalmente
  - Chiede di "pulire" o "montare" un video
  - Vuole aggiungere sottotitoli automatici
  - Richiede animazioni sincronizzate al parlato
  - Necessita export in multipli formati
  - Deve generare contenuti video da script/dialoghi
compatibility: |
  - FFmpeg (installato nel container)
  - Python 3.9+ (per script di processing)
  - ElevenLabs API key (fornita in config)
  - Librerie: moviepy, pydub, srt, webvtt, openai-whisper
---

# ONWAVE Video Assistant

Skill per la creazione di contenuti video professionali con sottotitoli automatici, animazioni e export multi-formato.

## Workflow Completo

```
1. VIDEO INTAKE
   ├─ Upload video grezzo
   ├─ Analisi durata, framerate, risoluzione
   └─ Validazione formato

2. AUDIO ANALYSIS
   ├─ Estrazione audio dal video
   ├─ Speech-to-text con Whisper (OpenAI)
   ├─ Generazione trascrizione temporizzata
   └─ Identificazione silenzi/pause

3. INTELLIGENT CUTTING
   ├─ Analisi contenuto e silenzi lunghi
   ├─ Identificazione parti "morte"
   ├─ Preview delle sezioni rimosse
   └─ Montaggio automatico con crossfade

4. SUBTITLE GENERATION
   ├─ Sincronizzazione trascrizione con timeline
   ├─ Generazione file .srt e .vtt
   ├─ Styling e posizionamento dinamico
   └─ Adattamento a testi lunghi/brevi

5. ANIMATION & EFFECTS
   ├─ Mapping animazioni al contenuto vocale
   ├─ Integrazione Hyperframes per transizioni
   ├─ Sincronizzazione keyframe con dettato
   └─ Layer compositing

6. AUDIO ENHANCEMENT
   ├─ Opzione: Sincronizza con voiceover ElevenLabs
   ├─ Livellamento audio
   ├─ Normalizzazione per consistency
   └─ Aggiunta musica/SFX (se richiesto)

7. EXPORT
   ├─ Render MP4 (H.264, AAC)
   ├─ Render WebM (VP9, Opus)
   ├─ Render MOV (ProRes, per post-production)
   └─ Generazione thumbnail/preview

8. OPTIMIZATION
   ├─ Compressione intelligente per piattaforma
   ├─ Validazione sincronizzazione A/V
   └─ Report qualità finale
```

## Comandi Disponibili

### 1. Analizza e Taglia Video
```
Analizza video grezzo, identifica parti morte, genera preview della versione editata
- Input: video file + opzioni cutting (rimozione silenzi, durata minima)
- Output: video editato + report analisi + timeline degli interventi
```

### 2. Genera Sottotitoli
```
Estrae speech-to-text e crea sottotitoli sincronizzati
- Input: video file
- Output: file .srt, .vtt + preview temporizzato
```

### 3. Applica Animazioni
```
Aggiunge animazioni dinamiche basate sul contenuto vocale
- Input: video + descrizione animazioni richieste
- Output: video con animazioni sincronizzate
```

### 4. Sincronizza con Voiceover ElevenLabs
```
Opzionale: genera voiceover di qualità cinema e sincronizza con video
- Input: script/testo + lingua + voce desiderata
- Output: video con nuovo audio sincronizzato
```

### 5. Export Multi-Formato
```
Renderizza in MP4, WebM, MOV con impostazioni optimizzate
- Input: video editato
- Output: 3 versioni in diversi formati + quality report
```

## Configurazione

### API Keys
```env
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY
OPENAI_API_KEY=sk_xxxx... # Per Whisper speech-to-text (opzionale, usa modello open-source se non fornito)
```

### Preferenze di Default
```python
# Cutting
SILENCE_THRESHOLD = -40  # dB
MIN_SILENCE_DURATION = 2.0  # secondi
REMOVE_SILENCE = True

# Subtitle Styling
FONT_SIZE = 48
FONT_FAMILY = "Arial"
FONT_COLOR = "#FFFFFF"
BACKGROUND_COLOR = "rgba(0,0,0,0.7)"
POSITION = "bottom"  # top, center, bottom

# Export
DEFAULT_BITRATE_MP4 = "8000k"
DEFAULT_BITRATE_WEBM = "6000k"
DEFAULT_FPS = 30
DEFAULT_RESOLUTION = "1920x1080"
```

## Utilizzo per ONWAVE

### Caso 1: Contenuto Social Media
```
1. Utente carica video grezzo di 15 minuti
2. Sistema rimuove automaticamente silenzi lunghi → 8 minuti
3. Aggiunge animazioni per engagement (zoom, pan, text overlays)
4. Genera sottotitoli per social (senza audio - silent video)
5. Export in 3 formati + versione verticale per TikTok/Reels
```

### Caso 2: Contenuto Educational/Tutorial
```
1. Utente carica screencast + voiceover
2. Sistema estrae audio, genera trascrizione
3. Sincronizza sottotitoli per accessibilità
4. Applica highlight boxes sugli elementi screencap
5. Aggiunge effetti Hyperframes per enfasi
6. Export in MP4 HD per sito + WebM compresso per streaming
```

### Caso 3: Branding/Corporate Video
```
1. Carica video intervista client
2. Pulisce audio, rimuove errori
3. Sincronizza logo/brand animations nel background
4. Aggiunge titoli e lower-thirds animati
5. Opzionale: ricrea voiceover con voice sintetizzata ElevenLabs (tono brand)
6. Export ProRes per post-production + MP4 delivery
```

## Limiti e Note

- **Risoluzione massima**: 4K (downscale automatico se superiore)
- **Durata massima**: 2 ore per file (split automatico se superiore)
- **Formati input supportati**: MP4, MOV, AVI, MKV, WebM
- **Sottotitoli**: auto-generated da audio ≥80% accuracy (Whisper)
- **Animazioni**: personalizzabili via JSON schema (vedi `references/hyperframes-schema.json`)

## Prossimi Step

1. Consulta `scripts/video-processor.py` per dettagli tecnici
2. Vedi `references/elevenlabs-integration.md` per voiceover avanzato
3. Leggi `references/hyperframes-animations.md` per custom animations
4. Scarica `assets/subtitle-templates.json` per styling presets

---

**Creata per ONWAVE** | Studio creativo specializzato in ecosistemi digitali ad alta performance
