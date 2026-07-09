# Hyperframes Animation Guide

Guida completa per creare animazioni dinamiche sincronizzate con il contenuto video.

## 📋 Indice

1. [Quick Start](#quick-start)
2. [Animation Types](#animation-types)
3. [Video Styles](#video-styles)
4. [JSON Schema](#json-schema)
5. [Examples](#examples)

---

## Quick Start

### Auto-Generate Animations

```bash
python scripts/animations.py
```

Questo genera automaticamente animazioni da subtitle usando il profilo "social_media".

### Custom Configuration

```python
from scripts.animations import AnimationGenerator, HyperframesGenerator

# Carica subtitle
subtitles = [
    {"start": 0, "end": 2, "text": "Intro"},
    {"start": 2, "end": 4, "text": "Content"},
    {"start": 4, "end": 6, "text": "Outro"},
]

# Genera animazioni
animations = AnimationGenerator.from_transcript(
    subtitles,
    video_style="social_media",
    intensity=0.9
)

# Esporta JSON
HyperframesGenerator.generate_json(animations, "animations.json")
```

---

## Animation Types

### 1. **Zoom** (Ingrandimento)

```json
{
  "type": "zoom_in",
  "target": "video",
  "startTime": 0,
  "duration": 0.5,
  "intensity": 0.8
}
```

- `zoom_in`: Avanza dalla periferia verso il centro
- `zoom_out`: Allontana dalla periferia
- **Intensity**: 0.0-1.0 (quanto grande lo zoom)
- **Use Case**: Enfasi, attention-grabbing, transizioni

### 2. **Pan** (Panoramica)

```json
{
  "type": "pan_left",
  "target": "background",
  "startTime": 2,
  "duration": 1.0,
  "intensity": 0.5
}
```

- `pan_left`: Muove lo sguardo da destra a sinistra
- `pan_right`: Muove da sinistra a destra
- **Use Case**: Reveal elementi, storyline, cinematic

### 3. **Fade** (Dissolvenza)

```json
{
  "type": "fade_in",
  "target": "subtitle_1",
  "startTime": 0,
  "duration": 0.3,
  "intensity": 1.0
}
```

- `fade_in`: Appare gradualmente
- `fade_out`: Scompare gradualmente
- **Intensity**: Velocità della dissolvenza
- **Use Case**: Transizioni smooth, intro/outro

### 4. **Slide** (Scorrimento)

```json
{
  "type": "slide_left",
  "target": "element",
  "startTime": 1,
  "duration": 0.4,
  "intensity": 0.7
}
```

- `slide_left`: Entra da destra, esce a sinistra
- `slide_right`: Entra da sinistra, esce a destra
- **Use Case**: Transizioni contenuto, reveal
- **Intensity**: Distanza dello slide

### 5. **Rotate** (Rotazione)

```json
{
  "type": "rotate",
  "target": "logo",
  "startTime": 0.5,
  "duration": 1.0,
  "intensity": 0.6,
  "properties": {
    "angle": 45,
    "direction": "clockwise"
  }
}
```

- **Properties**:
  - `angle`: Gradi di rotazione (0-360)
  - `direction`: "clockwise" o "counter_clockwise"
- **Use Case**: Logo, branding, enfasi dinamica

### 6. **Pulse** (Pulsazione)

```json
{
  "type": "pulse",
  "target": "highlight",
  "startTime": 1.5,
  "duration": 0.5,
  "intensity": 0.8
}
```

- Ritmo di importanza - elemento respira
- **Intensity**: Ampiezza della pulsazione
- **Use Case**: Attrazione attenzione, elemento importante

### 7. **Bounce** (Rimbalzo)

```json
{
  "type": "bounce",
  "target": "cta_button",
  "startTime": 2,
  "duration": 0.6,
  "intensity": 0.9
}
```

- Movimento rimbalzante verticale
- **Use Case**: Call-to-action, elemento interattivo

### 8. **Highlight** (Evidenziazione)

```json
{
  "type": "highlight",
  "target": "key_text",
  "startTime": 3,
  "duration": 1.0,
  "intensity": 0.7,
  "properties": {
    "color": "#FFD700",
    "blur": 2
  }
}
```

- Illumina/evidenzia elemento
- **Properties**:
  - `color`: Colore highlight (hex)
  - `blur`: Soft glow effect
- **Use Case**: Emphasis, focus sul testo

### 9. **Text Animations**

#### 9.1 Text Appear

```json
{
  "type": "text_appear",
  "target": "title",
  "startTime": 0,
  "duration": 0.3,
  "intensity": 1.0
}
```

Il testo appare tutto insieme, non dissolvenza.

#### 9.2 Text Typewriter

```json
{
  "type": "text_typewriter",
  "target": "subtitle",
  "startTime": 1,
  "duration": 2.0,
  "intensity": 0.8,
  "properties": {
    "speed": "medium",
    "sound": true
  }
}
```

Il testo appare carattere per carattere come da macchina da scrivere.

- **Properties**:
  - `speed`: "slow", "medium", "fast"
  - `sound`: true per aggiungere suono di digitazione

### 10. **Callout** (Evidenziazione scatola)

```json
{
  "type": "callout",
  "target": "important_area",
  "startTime": 2,
  "duration": 1.5,
  "intensity": 0.9,
  "properties": {
    "shape": "rect",
    "strokeColor": "#FF0000",
    "strokeWidth": 3
  }
}
```

Disegna scatola/evidenziazione attorno elemento.

- **Properties**:
  - `shape`: "rect", "circle", "rounded_rect"
  - `strokeColor`: Colore bordo (hex)
  - `strokeWidth`: Spessore bordo (pixel)

### 11. **Emphasis** (Enfasi)

```json
{
  "type": "emphasis",
  "target": "key_message",
  "startTime": 1.5,
  "duration": 0.8,
  "intensity": 1.0
}
```

Animazione generica di enfasi - combinazione di scale, brightness.

- **Use Case**: Momento importante del video

---

## Video Styles

ONWAVE include 5 profili di animazione predefiniti:

### 1. **Social Media** (Default)

```python
style = "social_media"
```

- **Caratteri**: Veloce, dinamica, attenzione
- **Durata animazioni**: 0.2-0.8 secondi
- **Intensità**: Alta (0.7-1.0)
- **Sequenza tipica**:
  1. Zoom in all'inizio
  2. Fade in elemento
  3. Emphasis durante il testo
  4. Zoom out per uscita
- **Target**: TikTok, Instagram, YouTube Shorts

### 2. **Educational**

```python
style = "educational"
```

- **Caratteri**: Calma, chiara, supporto visivo
- **Durata animazioni**: 0.5-2.0 secondi
- **Intensità**: Media (0.5-0.7)
- **Sequenza tipica**:
  1. Fade in smooth (0.5s)
  2. Highlight area rilevante
  3. Text typewriter per dettagli
  4. Fade out (0.5s)
- **Target**: Corsi online, tutorial, documentari

### 3. **Corporate**

```python
style = "corporate"
```

- **Caratteri**: Professionale, elegante, sofisticato
- **Durata animazioni**: 0.3-0.6 secondi
- **Intensità**: Bassa (0.3-0.5)
- **Sequenza tipica**:
  1. Slide left smooth
  2. Fade in delicato
  3. Callout su punto importante
  4. Fade out
- **Target**: Video aziendali, presentazioni B2B

### 4. **Testimonial**

```python
style = "testimonial"
```

- **Caratteri**: Caldo, personale, coinvolgente
- **Durata animazioni**: 0.4-0.8 secondi
- **Intensità**: Media (0.6-0.8)
- **Sequenza tipica**:
  1. Zoom in leggero (0.3x)
  2. Fade in della persona
  3. Pulse durante la citazione
  4. Bounce su CTA
- **Target**: Case studies, review, customer stories

### 5. **Action**

```python
style = "action"
```

- **Caratteri**: Energia, movimento, dinamica pura
- **Durata animazioni**: 0.1-0.4 secondi
- **Intensità**: Massima (0.9-1.0)
- **Sequenza tipica**:
  1. Zoom in aggressivo
  2. Rotate elemento
  3. Pan movimento
  4. Emphasis e transizione
- **Target**: Trailer, promo, video gaming

---

## JSON Schema

### Complete Hyperframes JSON

```json
{
  "version": "1.0",
  "project": {
    "name": "Video Project Name",
    "fps": 30,
    "duration": 120
  },
  "layers": [
    {
      "id": "video_layer",
      "name": "Main Video",
      "type": "video",
      "startTime": 0,
      "duration": 120
    },
    {
      "id": "subtitle_layer",
      "name": "Subtitles",
      "type": "text",
      "startTime": 0,
      "duration": 120
    }
  ],
  "timeline": [
    {
      "id": "anim_001",
      "type": "zoom_in",
      "target": "video_layer",
      "startTime": 0,
      "duration": 0.5,
      "easing": "ease-in-out",
      "intensity": 0.8,
      "properties": {
        "scale_start": 1.0,
        "scale_end": 1.2
      }
    },
    {
      "id": "anim_002",
      "type": "text_typewriter",
      "target": "subtitle_layer",
      "startTime": 0.5,
      "duration": 2.0,
      "easing": "linear",
      "intensity": 1.0,
      "properties": {
        "speed": "medium",
        "sound": true
      }
    }
  ]
}
```

### Schema Properties

| Property | Type | Required | Default | Notes |
|---|---|---|---|---|
| `version` | string | Yes | - | "1.0" per compatibilità |
| `project.name` | string | Yes | - | Nome identificativo |
| `project.fps` | number | Yes | 30 | Frame per secondo |
| `project.duration` | number | Yes | - | Durata totale in secondi |
| `layers` | array | No | [] | Layer video/testo |
| `timeline` | array | Yes | [] | Elenco animazioni |
| `id` | string | Yes | - | Unique identifier |
| `type` | string | Yes | - | Tipo animazione (vedi sopra) |
| `target` | string | Yes | - | Layer/elemento da animare |
| `startTime` | number | Yes | - | Inizio animazione (sec) |
| `duration` | number | Yes | - | Durata animazione (sec) |
| `easing` | string | No | "ease-in-out" | Curva interpolazione |
| `intensity` | number | No | 1.0 | Forza 0.0-1.0 |
| `properties` | object | No | {} | Parametri custom |

### Easing Functions

```
- "linear": Velocità costante
- "ease-in": Accelerazione
- "ease-out": Decelerazione
- "ease-in-out": Accelera poi decelera (DEFAULT)
- "ease-in-cubic": Accelerazione forte
- "ease-out-cubic": Decelerazione forte
- "ease-in-elastic": Effetto elastico in entrata
- "ease-out-elastic": Effetto elastico in uscita
```

---

## Examples

### Example 1: Social Media Video (15 secondi)

```python
subtitles = [
    {"start": 0, "end": 3, "text": "Problem Highlight"},
    {"start": 3, "end": 6, "text": "Solution Introduction"},
    {"start": 6, "end": 9, "text": "Benefit Explanation"},
    {"start": 9, "end": 12, "text": "CTA Message"},
]

animations = AnimationGenerator.from_transcript(
    subtitles,
    video_style="social_media",
    intensity=0.95
)

HyperframesGenerator.generate_json(animations, "social.json")
```

Output:
- Zoom in + fade per ogni sezione
- Pulse durante messages chiave
- Emphasis finale su CTA

### Example 2: Keyword-Based Animations

```python
keyword_animations = {
    "importante": "highlight",
    "veloce": "zoom_in",
    "calma": "fade_in",
    "clicca": "bounce",
}

animations = AnimationGenerator.from_keywords(
    script_text="Questo è importante! Azione veloce. Rimani calma. Clicca qui!",
    subtitles=subtitles,
    keyword_animations=keyword_animations
)
```

### Example 3: Educational Tutorial (3 minuti)

```python
animations = AnimationGenerator.from_transcript(
    subtitles,
    video_style="educational",
    intensity=0.6
)

# Aggiungi callout su aree specifiche
callout_anim = Animation(
    type=AnimationType.CALLOUT,
    target="ui_element",
    start_time=15.0,
    duration=3.0,
    intensity=0.8,
    params={"shape": "rect", "strokeColor": "#FF0000"}
)

animations.append(callout_anim)
HyperframesGenerator.generate_json(animations, "tutorial.json")
```

---

## Tips & Tricks

### 1. Timing Perfetto

```python
# Sincronizza animazione con voce
for sub in subtitles:
    # Animation inizia quando parla
    anim.start_time = sub["start"] + 0.1  # Small delay
    # Finisce poco prima della prossima
    anim.duration = (sub["end"] - sub["start"]) - 0.2
```

### 2. Layering Animations

```python
# Crea effetto cascata
start_time = 0
for i, element in enumerate(elements):
    anim = Animation(
        type=AnimationType.SLIDE_LEFT,
        target=element,
        start_time=start_time + (i * 0.2),  # Staggered
        duration=0.5
    )
    animations.append(anim)
```

### 3. Combining Effects

```python
# Zoom + Rotate per logo spin
animations.append(Animation(
    type=AnimationType.ZOOM_IN,
    target="logo",
    start_time=0,
    duration=0.3
))
animations.append(Animation(
    type=AnimationType.ROTATE,
    target="logo",
    start_time=0.15,  # Start mid-zoom
    duration=0.4,
    params={"angle": 360, "direction": "clockwise"}
))
```

---

**Hyperframes Docs**: https://hyperframes.io/docs
**Animation Best Practices**: https://www.anandtech.com/show/video-editing-basics
