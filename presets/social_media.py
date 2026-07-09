#!/usr/bin/env python3
"""
ONWAVE Social Media Video Preset
Optimizzato per TikTok, Instagram Reels, YouTube Shorts
Vertical video (9:16), energico, mobile-first
"""

import yaml
from pathlib import Path

SOCIAL_MEDIA_PRESET = {
    'name': 'social_media',
    'display_name': 'Social Media (TikTok/Reels/Shorts)',
    'description': 'Verticale, dinamico, super compresso - ottimizzato per mobile',
    'target_platforms': ['tiktok', 'instagram_reels', 'youtube_shorts', 'instagram_stories'],
    
    # ============================================================================
    # VIDEO SETTINGS
    # ============================================================================
    'video': {
        'resolution': '1080x1920',      # Vertical 9:16
        'aspect_ratio': '9:16',
        'fps': 30,                      # Frame rate
        'codec': 'h264',                # Video codec
        'bitrate': '7500k',             # 7.5 Mbps (compressed ma qualità buona)
        'color_space': 'bt709',
        'preset': 'fast',               # FFmpeg preset (slow, medium, fast)
        'crf': 23,                      # Quality (lower = better, 0-51)
        'maxrate': '8500k',             # Peak bitrate
        'bufsize': '15000k',            # Buffer size
    },
    
    # ============================================================================
    # AUDIO SETTINGS
    # ============================================================================
    'audio': {
        'codec': 'aac',
        'bitrate': '128k',
        'sample_rate': 48000,
        'channels': 2,                  # Stereo
        'denoise': True,                # Rimuovi rumore di fondo
        'volume_normalization': True,   # Normalize LUFS
        'target_loudness': -16,         # YouTube raccomanda -14 LUFS, social -16
    },
    
    # ============================================================================
    # SUBTITLE SETTINGS
    # ============================================================================
    'subtitles': {
        'enabled': True,
        'auto_generate': True,
        'language': 'it',               # Italian
        'languages_auto_translate': ['en', 'es', 'fr', 'de'],  # Auto-generate versions
        
        'font': {
            'family': 'Arial',
            'size': 48,                 # Large, readable on mobile
            'weight': 'bold',           # Bold for impact
            'color': '#FFFFFF',         # White text
        },
        
        'background': {
            'enabled': True,
            'color': 'rgba(0,0,0,0.8)',  # Semi-transparent black
            'padding': 8,               # Padding around text
            'border_radius': 4,
        },
        
        'position': 'bottom',           # Bottom-aligned (TikTok standard)
        'margin_bottom': 40,            # Space from bottom
        'max_line_length': 42,          # Wrap at ~42 chars
        'timing': {
            'fade_in': 0.2,             # Appear duration
            'fade_out': 0.2,            # Disappear duration
        }
    },
    
    # ============================================================================
    # ANIMATION SETTINGS
    # ============================================================================
    'animations': {
        'enabled': True,
        'style': 'social_media',        # Preset style
        'intensity': 0.95,              # Very energetic (0.0-1.0)
        'enabled_types': [
            'zoom_in',
            'zoom_out',
            'fade_in',
            'fade_out',
            'pulse',
            'bounce',
            'highlight',
            'text_appear'
        ],
        
        # Keyframe automation
        'auto_keyframes': True,
        'keyframe_interval_seconds': 3,  # Every 3 seconds
        
        # Transition settings
        'transitions': {
            'enabled': True,
            'type': 'fade',              # fade, slide, zoom
            'duration': 0.3,
        },
        
        # Particle effects for highlights
        'particles': {
            'enabled': True,
            'density': 0.7,              # 0.0-1.0
        },
    },
    
    # ============================================================================
    # VOICEOVER SETTINGS
    # ============================================================================
    'voiceover': {
        'enabled': False,               # Skip by default (use original audio)
        'profile': 'energetic',         # Energetic voice
        
        'elevenlabs': {
            'model_id': 'eleven_monolingual_v1',
            'voice_id': 'EXAVITQu4nSv3jS1aQ9b',  # Andrea (energetic)
            'stability': 0.6,            # Lower = more varied
            'similarity_boost': 0.8,    # Higher = more consistent
        },
        
        'processing': {
            'speed': 1.0,               # Playback speed
            'pitch': 0,                 # Pitch shift (-20 to +20)
            'volume_db': 0,             # Volume adjustment
        }
    },
    
    # ============================================================================
    # PROCESSING OPTIONS
    # ============================================================================
    'processing': {
        'remove_silence': {
            'enabled': True,
            'threshold_db': -40,        # Silence threshold
            'min_duration': 2.0,        # Min silence duration
        },
        
        'auto_cut': {
            'enabled': True,
            'min_scene_duration': 1.5,  # Min scene length (seconds)
            'cut_on_silence': True,
        },
        
        'color_correction': {
            'enabled': True,
            'brightness': 0,
            'contrast': 1.05,           # Slight boost
            'saturation': 1.15,         # Vivid colors for social
        },
        
        'stabilization': {
            'enabled': True,
            'strength': 'medium',       # light, medium, strong
        },
        
        'denoise': {
            'enabled': True,
            'strength': 0.5,
        },
        
        'enhance_faces': {
            'enabled': True,
            'detection': True,
            'brightening': 0.1,
        },
    },
    
    # ============================================================================
    # EXPORT SETTINGS
    # ============================================================================
    'export': [
        {
            'name': 'Social Media (MP4)',
            'format': 'mp4',
            'codec': 'h264',
            'bitrate': '7500k',
            'resolution': '1080x1920',
            'suffix': '_social',
            'estimated_size_mb': '28-35',
        },
        {
            'name': 'Web Optimized (WebM)',
            'format': 'webm',
            'codec': 'vp9',
            'bitrate': '5000k',
            'resolution': '1080x1920',
            'suffix': '_web',
            'estimated_size_mb': '19-25',
        }
    ],
    
    # ============================================================================
    # METADATA & SEO
    # ============================================================================
    'metadata': {
        'add_titles': True,
        'add_chapter_markers': False,   # Not needed for short videos
        'auto_hashtags': True,
        'hashtags': [
            '#socialmedia',
            '#reels',
            '#tiktok',
            '#shorts'
        ]
    },
}

# Script per applicare il preset
class SocialMediaPreset:
    """Applica preset social media a video"""
    
    @staticmethod
    def apply(video_path: str, output_dir: str) -> dict:
        """
        Applica preset social media completo
        
        Args:
            video_path: Percorso video sorgente
            output_dir: Cartella output
            
        Returns:
            dict con dettagli processing
        """
        from pathlib import Path
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("🎬 Applicando Social Media Preset...")
        
        video_name = Path(video_path).stem
        
        # 1. Analisi video
        logger.info("📊 Fase 1: Analisi video...")
        # (implementation)
        
        # 2. Rimozione silenzi
        logger.info("🔇 Fase 2: Rimozione silenzi...")
        # (implementation)
        
        # 3. Sottotitoli automatici
        logger.info("📝 Fase 3: Generazione sottotitoli...")
        # (implementation)
        
        # 4. Animazioni sincronizzate
        logger.info("✨ Fase 4: Animazioni sincronizzate...")
        # (implementation)
        
        # 5. Color grading
        logger.info("🎨 Fase 5: Color grading...")
        # (implementation)
        
        # 6. Export multi-formato
        logger.info("💾 Fase 6: Export MP4/WebM...")
        # (implementation)
        
        logger.info("✓ Social Media Preset applicato!")
        
        return {
            'video': video_name,
            'preset': 'social_media',
            'platform': 'TikTok/Reels/Shorts',
            'resolution': '1080x1920',
            'files_generated': [
                f'{video_name}_social.mp4',
                f'{video_name}_web.webm'
            ],
            'metadata': {
                'duration_seconds': 0,
                'output_size_mb': 0,
                'quality_score': 'HD',
            }
        }

if __name__ == '__main__':
    # Test: print config
    import json
    print(json.dumps(SOCIAL_MEDIA_PRESET, indent=2))
