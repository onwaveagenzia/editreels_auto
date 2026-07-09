#!/usr/bin/env python3
"""
ONWAVE Social Media Video Preset
Optimized for TikTok, Instagram Reels, YouTube Shorts
- 1080×1920 @ 9:16 aspect ratio
- 7500k bitrate optimizzato
- Animazioni energiche 0.95 intensity
- Sottotitoli brevi e impattanti
- Silenzi rimossi aggressivamente
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class SocialMediaPreset:
    """Configurazione completa per social media video"""
    
    # Video Output
    resolution_width: int = 1080
    resolution_height: int = 1920
    aspect_ratio: str = "9:16"
    fps: int = 30
    bitrate: str = "7500k"
    format_mp4_codec: str = "libx264"
    format_mp4_preset: str = "fast"  # fast, medium, slow
    format_webm_codec: str = "libvpx-vp9"
    format_mov_codec: str = "prores"
    
    # Audio
    audio_bitrate: str = "192k"
    audio_sample_rate: int = 44100
    
    # Silence Detection
    silence_detection_enabled: bool = True
    silence_db_threshold: float = -35.0  # More aggressive than default -40dB
    silence_min_duration: float = 1.0  # Remove silences > 1 second
    
    # Subtitle Generation
    subtitles_enabled: bool = True
    subtitles_format: str = "srt"  # srt, vtt, ass
    subtitle_font_size: int = 32
    subtitle_font_color: str = "white"
    subtitle_bg_color: str = "black_with_transparency"
    subtitle_bg_padding: int = 10
    subtitle_placement: str = "bottom"  # top, bottom, center
    subtitle_max_chars_per_line: int = 35
    
    # Animations (Hyperframes)
    animations_enabled: bool = True
    animation_intensity: float = 0.95  # 0.0-1.0, high for social media
    animation_intensity_on_speech: float = 0.85
    animation_styles: List[str] = None
    animation_keywords: List[str] = None
    animation_duration_per_keyframe: float = 0.5  # seconds
    
    # Dynamics & Effects
    dynamic_zoom: bool = True
    zoom_speed: float = 1.2
    color_grading: bool = True
    color_preset: str = "vibrant"  # vivid, balanced, warm, cool, vibrant
    sharpness_boost: float = 1.15
    contrast_boost: float = 1.1
    saturation_boost: float = 1.2
    
    # Voice & Audio
    voice_synthesis_enabled: bool = False
    voice_profile: Optional[str] = None  # professional, warm, energetic, deep
    background_music_volume: float = 0.3
    voice_volume: float = 1.0
    
    # Text Overlays
    text_overlays_enabled: bool = True
    text_overlay_style: str = "modern"  # modern, bold, casual, elegant
    text_animation: str = "slide_in"  # fade_in, slide_in, pop, typewriter
    text_color: str = "white"
    text_bg: bool = True
    text_shadow: bool = True
    
    # Output Optimization
    output_formats: List[str] = None
    optimize_for_platform: str = "tiktok"  # tiktok, instagram, youtube
    enable_adaptive_bitrate: bool = True
    enable_scene_detection: bool = True
    
    def __post_init__(self):
        if self.animation_styles is None:
            self.animation_styles = [
                "zoom_in_on_speech",
                "slide_left",
                "slide_right",
                "pop",
                "fade_transitions",
                "color_flash"
            ]
        
        if self.animation_keywords is None:
            self.animation_keywords = [
                "intro", "highlight", "important",
                "question", "reveal", "emphasis"
            ]
        
        if self.output_formats is None:
            self.output_formats = ["mp4"]  # Primary format
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for config file"""
        return {
            "name": "Social Media",
            "description": "Optimized for TikTok, Instagram Reels, YouTube Shorts",
            "video": {
                "resolution": f"{self.resolution_width}x{self.resolution_height}",
                "aspect_ratio": self.aspect_ratio,
                "fps": self.fps,
                "bitrate": self.bitrate,
                "codec_mp4": self.format_mp4_codec,
                "preset": self.format_mp4_preset,
                "codec_webm": self.format_webm_codec
            },
            "audio": {
                "bitrate": self.audio_bitrate,
                "sample_rate": self.audio_sample_rate
            },
            "silence": {
                "enabled": self.silence_detection_enabled,
                "threshold_db": self.silence_db_threshold,
                "min_duration_seconds": self.silence_min_duration
            },
            "subtitles": {
                "enabled": self.subtitles_enabled,
                "format": self.subtitles_format,
                "font_size": self.subtitle_font_size,
                "color": self.subtitle_font_color,
                "placement": self.subtitle_placement,
                "max_chars_per_line": self.subtitle_max_chars_per_line
            },
            "animations": {
                "enabled": self.animations_enabled,
                "intensity": self.animation_intensity,
                "intensity_on_speech": self.animation_intensity_on_speech,
                "styles": self.animation_styles,
                "keywords": self.animation_keywords
            },
            "effects": {
                "dynamic_zoom": self.dynamic_zoom,
                "zoom_speed": self.zoom_speed,
                "color_grading": self.color_grading,
                "color_preset": self.color_preset,
                "sharpness": self.sharpness_boost,
                "contrast": self.contrast_boost,
                "saturation": self.saturation_boost
            },
            "voice": {
                "synthesis_enabled": self.voice_synthesis_enabled,
                "background_music_volume": self.background_music_volume
            },
            "text_overlays": {
                "enabled": self.text_overlays_enabled,
                "style": self.text_overlay_style,
                "animation": self.text_animation
            },
            "output": {
                "formats": self.output_formats,
                "optimize_for": self.optimize_for_platform,
                "adaptive_bitrate": self.enable_adaptive_bitrate,
                "scene_detection": self.enable_scene_detection
            }
        }

# ============================================================================
# PRESET PROCESSOR
# ============================================================================

class SocialMediaProcessor:
    """Elabora video usando preset social media"""
    
    def __init__(self, preset: SocialMediaPreset):
        self.preset = preset
    
    def analyze_video(self, video_path: str) -> Dict:
        """Analizza video per ottimizzazioni"""
        import subprocess
        
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-of', 'json',
            video_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {}
        
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        
        if not streams:
            return {}
        
        video_stream = next((s for s in streams if s.get('width')), None)
        audio_stream = next((s for s in streams if 'sample_rate' in s), None)
        
        analysis = {
            'width': video_stream.get('width') if video_stream else 0,
            'height': video_stream.get('height') if video_stream else 0,
            'duration': float(video_stream.get('duration', 0)) if video_stream else 0,
            'fps': eval(video_stream.get('r_frame_rate', '30/1')) if video_stream else 30,
            'has_audio': bool(audio_stream)
        }
        
        # Detect if vertical video
        if analysis['height'] > analysis['width']:
            analysis['is_vertical'] = True
            analysis['aspect_ratio'] = f"{analysis['width']}:{analysis['height']}"
        
        return analysis
    
    def generate_ffmpeg_command(self, input_path: str, output_path: str, 
                               analysis: Dict) -> List[str]:
        """Genera comando FFmpeg ottimizzato"""
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            
            # Resize & scale
            '-vf', (
                f"scale={self.preset.resolution_width}:{self.preset.resolution_height},"
                f"fps={self.preset.fps},"
                # Color grading
                f"eq=saturation={self.preset.saturation_boost}:"
                f"contrast={self.preset.contrast_boost}"
            ),
            
            # Video codec
            '-c:v', self.preset.format_mp4_codec,
            '-preset', self.preset.format_mp4_preset,
            '-b:v', self.preset.bitrate,
            
            # Audio codec
            '-c:a', 'aac',
            '-b:a', self.preset.audio_bitrate,
            '-ar', str(self.preset.audio_sample_rate),
            
            # Optimization
            '-pix_fmt', 'yuv420p',  # H.264 compatibility
            '-movflags', '+faststart',  # Enable streaming
            
            output_path
        ]
        
        return cmd
    
    def get_subtitle_config(self) -> Dict:
        """Configurazione sottotitoli per social media"""
        return {
            'format': self.preset.subtitles_format,
            'font_size': self.preset.subtitle_font_size,
            'color': self.preset.subtitle_font_color,
            'placement': self.preset.subtitle_placement,
            'max_length': self.preset.subtitle_max_chars_per_line,
            'style': {
                'bold': True,
                'background': True,
                'shadow': True
            }
        }
    
    def get_animation_config(self) -> Dict:
        """Configurazione animazioni Hyperframes"""
        return {
            'enabled': self.preset.animations_enabled,
            'intensity': self.preset.animation_intensity,
            'intensity_on_speech': self.preset.animation_intensity_on_speech,
            'styles': self.preset.animation_styles,
            'keywords': self.preset.animation_keywords,
            'trigger_on_silence_removal': True,
            'trigger_on_subtitle': True,
            'trigger_on_speech': True
        }

# ============================================================================
# CONFIG FILE GENERATOR
# ============================================================================

def generate_social_preset_config() -> Dict:
    """Genera file di configurazione completo"""
    
    preset = SocialMediaPreset()
    
    return {
        "presets": {
            "social_media": preset.to_dict()
        },
        "guidelines": {
            "video_duration": {
                "optimal_range": "15-60 seconds",
                "tiktok": "up to 10 minutes",
                "instagram_reels": "up to 90 seconds",
                "youtube_shorts": "up to 60 seconds"
            },
            "best_practices": [
                "Hook viewers in first 1-2 seconds",
                "Use subtitles for 100% audio clarity",
                "Animate text for emphasis",
                "Remove all dead air/silence",
                "Use vertical (9:16) format",
                "Keep motion constant and engaging",
                "Use bright, saturated colors",
                "Include CTA (Call To Action)"
            ],
            "color_grading_tips": [
                "Increase saturation by 20% for social",
                "Boost contrast for better readability",
                "Use warm tones for storytelling",
                "Cool tones for professional/corporate",
                "Vibrant for maximum engagement"
            ]
        }
    }

# ============================================================================
# EXPORT
# ============================================================================

if __name__ == '__main__':
    # Generate and save config
    config = generate_social_preset_config()
    
    config_path = Path('config-social-preset.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Social Media Preset config saved to {config_path}")
    print(json.dumps(config, indent=2))
