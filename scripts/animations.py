#!/usr/bin/env python3
"""
ONWAVE Animation Engine
Applica animazioni Hyperframes sincronizzate con audio/testo.
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ANIMATION TYPES
# ============================================================================

class AnimationType(Enum):
    """Tipi di animazioni supportate"""
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ROTATE = "rotate"
    PULSE = "pulse"
    BOUNCE = "bounce"
    HIGHLIGHT = "highlight"
    TEXT_APPEAR = "text_appear"
    TEXT_TYPEWRITER = "text_typewriter"
    CALLOUT = "callout"
    EMPHASIS = "emphasis"

@dataclass
class Animation:
    """Definizione animazione"""
    type: AnimationType
    target: str  # Elemento/layer da animare
    start_time: float  # Secondi
    duration: float  # Secondi
    intensity: float = 1.0  # 0.0 - 1.0
    easing: str = "ease-in-out"
    params: Dict = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

# ============================================================================
# ANIMATION PROFILES
# ============================================================================

class AnimationProfiles:
    """Profili di animazione predefiniti per tipologie di contenuto"""
    
    # Social Media: veloce, dinamica, attenzione
    SOCIAL_MEDIA = [
        {"type": "zoom_in", "duration": 0.3, "intensity": 0.7},
        {"type": "fade_in", "duration": 0.2},
        {"type": "emphasis", "duration": 0.8},
        {"type": "zoom_out", "duration": 0.3},
    ]
    
    # Educational: calma, chiara, supporto visivo
    EDUCATIONAL = [
        {"type": "fade_in", "duration": 0.5},
        {"type": "highlight", "duration": 2.0},
        {"type": "text_typewriter", "duration": 1.5},
        {"type": "fade_out", "duration": 0.5},
    ]
    
    # Corporate: professionale, elegante, sofisticato
    CORPORATE = [
        {"type": "slide_left", "duration": 0.4, "intensity": 0.5},
        {"type": "fade_in", "duration": 0.3},
        {"type": "callout", "duration": 0.6},
        {"type": "fade_out", "duration": 0.4},
    ]
    
    # Testimonial: caldo, personale, coinvolgente
    TESTIMONIAL = [
        {"type": "zoom_in", "duration": 0.5, "intensity": 0.3},
        {"type": "fade_in", "duration": 0.4},
        {"type": "pulse", "duration": 0.3},
        {"type": "bounce", "duration": 0.5},
    ]
    
    # Action: energia, movimento, dinamica
    ACTION = [
        {"type": "zoom_in", "duration": 0.2, "intensity": 1.0},
        {"type": "rotate", "duration": 0.4},
        {"type": "pan_right", "duration": 0.6},
        {"type": "emphasis", "duration": 0.3},
    ]

# ============================================================================
# ANIMATION GENERATOR
# ============================================================================

class AnimationGenerator:
    """Genera animazioni basate su timing e contenuto"""
    
    @staticmethod
    def from_transcript(
        subtitles: List[Dict],
        video_style: str = "social_media",
        intensity: float = 1.0
    ) -> List[Animation]:
        """Genera animazioni da trascrizione"""
        
        animations = []
        
        # Seleziona profilo
        profile_map = {
            "social_media": AnimationProfiles.SOCIAL_MEDIA,
            "educational": AnimationProfiles.EDUCATIONAL,
            "corporate": AnimationProfiles.CORPORATE,
            "testimonial": AnimationProfiles.TESTIMONIAL,
            "action": AnimationProfiles.ACTION,
        }
        profile = profile_map.get(video_style, AnimationProfiles.SOCIAL_MEDIA)
        
        # Applica animazioni a ogni subtitle
        for i, sub in enumerate(subtitles):
            start = sub["start"]
            duration = sub["end"] - sub["start"]
            
            # Baseline: fade in all'inizio
            animations.append(Animation(
                type=AnimationType.FADE_IN,
                target=f"subtitle_{i}",
                start_time=start,
                duration=0.2,
                intensity=intensity * 0.8
            ))
            
            # Animazione principale
            if i % 3 == 0:
                anim_type = AnimationType.ZOOM_IN
            elif i % 3 == 1:
                anim_type = AnimationType.SLIDE_LEFT
            else:
                anim_type = AnimationType.EMPHASIS
            
            animations.append(Animation(
                type=anim_type,
                target=f"subtitle_{i}",
                start_time=start,
                duration=duration * 0.3,
                intensity=intensity
            ))
            
            # Fade out alla fine
            if i < len(subtitles) - 1:
                animations.append(Animation(
                    type=AnimationType.FADE_OUT,
                    target=f"subtitle_{i}",
                    start_time=sub["end"] - 0.2,
                    duration=0.2,
                    intensity=intensity * 0.6
                ))
        
        logger.info(f"✓ {len(animations)} animazioni generate da {len(subtitles)} subtitle")
        return animations
    
    @staticmethod
    def from_keywords(
        text: str,
        subtitles: List[Dict],
        keyword_animations: Dict[str, str]
    ) -> List[Animation]:
        """Genera animazioni basate su keyword nel testo"""
        
        animations = []
        
        for sub in subtitles:
            text_lower = sub.get("text", "").lower()
            
            for keyword, anim_type in keyword_animations.items():
                if keyword.lower() in text_lower:
                    try:
                        anim = AnimationType[anim_type.upper()]
                        animations.append(Animation(
                            type=anim,
                            target=f"keyword_{keyword}",
                            start_time=sub["start"],
                            duration=sub["end"] - sub["start"],
                            intensity=1.0
                        ))
                        logger.info(f"✓ Animazione '{anim_type}' per keyword '{keyword}'")
                    except KeyError:
                        logger.warning(f"⚠️  Tipo animazione non valido: {anim_type}")
        
        return animations

# ============================================================================
# HYPERFRAMES JSON GENERATOR
# ============================================================================

class HyperframesGenerator:
    """Genera JSON compatibile con Hyperframes"""
    
    @staticmethod
    def generate_json(animations: List[Animation], output_path: str = "animations.json") -> str:
        """Converte animazioni in JSON Hyperframes"""
        
        hyperframes_json = {
            "version": "1.0",
            "project": {
                "name": "ONWAVE Video",
                "fps": 30,
                "duration": 0
            },
            "layers": [],
            "timeline": []
        }
        
        # Calcola durata massima
        if animations:
            max_time = max(a.start_time + a.duration for a in animations)
            hyperframes_json["project"]["duration"] = max_time
        
        # Aggiungi animazioni
        for anim in animations:
            timeline_entry = {
                "id": f"{anim.target}_{anim.type.value}",
                "type": anim.type.value,
                "target": anim.target,
                "startTime": anim.start_time,
                "duration": anim.duration,
                "easing": anim.easing,
                "intensity": anim.intensity,
                "properties": anim.params
            }
            hyperframes_json["timeline"].append(timeline_entry)
        
        # Salva JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(hyperframes_json, f, indent=2)
        
        logger.info(f"✓ Hyperframes JSON generato: {output_path}")
        return output_path
    
    @staticmethod
    def generate_ffmpeg_complex_filter(animations: List[Animation]) -> str:
        """Genera filtro FFmpeg da animazioni"""
        
        filters = []
        
        for anim in animations:
            if anim.type == AnimationType.ZOOM_IN:
                # zoom: scale=w/h:1
                scale_factor = 1.0 + (anim.intensity * 0.5)
                filters.append(f"scale=iw*{scale_factor}:ih*{scale_factor}")
            
            elif anim.type == AnimationType.ZOOM_OUT:
                scale_factor = 1.0 - (anim.intensity * 0.3)
                filters.append(f"scale=iw*{scale_factor}:ih*{scale_factor}")
            
            elif anim.type == AnimationType.FADE_IN:
                filters.append("fade=t=in:st=0:d=0.5")
            
            elif anim.type == AnimationType.FADE_OUT:
                filters.append("fade=t=out:st=0:d=0.5")
            
            elif anim.type == AnimationType.PAN_LEFT:
                filters.append("hflip")  # Mock
            
            elif anim.type == AnimationType.ROTATE:
                angle = 45 * anim.intensity
                filters.append(f"rotate={angle}")
        
        return ",".join(filters) if filters else "copy"

# ============================================================================
# ANIMATION PRESET MANAGER
# ============================================================================

class AnimationPresetManager:
    """Gestisce preset di animazioni"""
    
    PRESETS = {
        "intro": [
            {"type": "zoom_in", "duration": 0.5},
            {"type": "fade_in", "duration": 0.3},
        ],
        "emphasis": [
            {"type": "pulse", "duration": 0.4},
            {"type": "bounce", "duration": 0.3},
        ],
        "transition": [
            {"type": "fade_out", "duration": 0.2},
            {"type": "slide_left", "duration": 0.3},
            {"type": "fade_in", "duration": 0.2},
        ],
        "callout": [
            {"type": "highlight", "duration": 0.5},
            {"type": "emphasis", "duration": 0.4},
        ],
        "smooth": [
            {"type": "fade_in", "duration": 0.5},
            {"type": "slide_right", "duration": 0.3},
            {"type": "fade_out", "duration": 0.5},
        ]
    }
    
    @staticmethod
    def get_preset(name: str) -> List[Dict]:
        """Carica preset animazione"""
        if name not in AnimationPresetManager.PRESETS:
            logger.warning(f"Preset '{name}' non trovato, uso 'smooth'")
            return AnimationPresetManager.PRESETS["smooth"]
        return AnimationPresetManager.PRESETS[name]
    
    @staticmethod
    def list_presets() -> Dict:
        """Elenca tutti i preset"""
        return list(AnimationPresetManager.PRESETS.keys())

# ============================================================================
# CLI DEMO
# ============================================================================

if __name__ == "__main__":
    # Demo: genera animazioni da subtitle mock
    mock_subtitles = [
        {"start": 0, "end": 2, "text": "Benvenuto al video"},
        {"start": 2, "end": 4, "text": "Scopri le animazioni"},
        {"start": 4, "end": 6, "text": "Create per l'engagement"},
    ]
    
    print("\n🎬 ONWAVE Animation Generator\n")
    
    # Genera da profilo
    print("📊 Generazione animazioni da profilo 'social_media'...")
    animations = AnimationGenerator.from_transcript(
        mock_subtitles,
        video_style="social_media",
        intensity=0.9
    )
    
    print(f"✓ {len(animations)} animazioni generate\n")
    
    # Esporta in Hyperframes JSON
    json_path = HyperframesGenerator.generate_json(animations)
    
    # Leggi e stampa
    with open(json_path, 'r') as f:
        data = json.load(f)
        print(f"✓ Hyperframes JSON ({len(data['timeline'])} keyframe):")
        for anim in data['timeline'][:3]:
            print(f"  - {anim['type']}: {anim['target']} @ {anim['startTime']}s")
    
    print(f"\n✅ Output salvato: {json_path}")
