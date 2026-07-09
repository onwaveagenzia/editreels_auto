#!/usr/bin/env python3
"""
ONWAVE Video Processing CLI
Interactive workflow with menu-driven interface
"""

import click
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import subprocess
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.layout import Layout
except ImportError:
    print("⚠️  Installa rich: pip install rich")
    sys.exit(1)

console = Console()

# ============================================================================
# CONFIGURATION & STATE
# ============================================================================

CONFIG_DIR = Path.home() / ".onwave"
CONFIG_FILE = CONFIG_DIR / "config.json"
JOBS_FILE = CONFIG_DIR / "jobs.json"

DEFAULT_CONFIG = {
    "api_url": "http://localhost:5000",
    "google_drive_enabled": False,
    "google_drive_folder_id": None,
    "default_preset": "social_media",
    "last_output_dir": str(Path.home() / "OnwaveOutput"),
    "api_key": None
}

@dataclass
class VideoJob:
    job_id: str
    video_path: str
    preset: str
    status: str  # queued, processing, completed, error
    created: str
    output_dir: Optional[str] = None
    error_message: Optional[str] = None
    results: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_config() -> Dict:
    """Carica configurazione da file"""
    CONFIG_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict):
    """Salva configurazione"""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_jobs() -> Dict[str, VideoJob]:
    """Carica storico job"""
    if JOBS_FILE.exists():
        with open(JOBS_FILE) as f:
            data = json.load(f)
            return {
                jid: VideoJob(**jdata)
                for jid, jdata in data.items()
            }
    return {}

def save_jobs(jobs: Dict[str, VideoJob]):
    """Salva storico job"""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(JOBS_FILE, 'w') as f:
        json.dump({
            jid: asdict(job)
            for jid, job in jobs.items()
        }, f, indent=2, default=str)

def validate_video(video_path: str) -> bool:
    """Valida file video"""
    path = Path(video_path)
    if not path.exists():
        console.print(f"❌ File non trovato: {video_path}")
        return False
    
    valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
    if path.suffix.lower() not in valid_extensions:
        console.print(f"❌ Formato non supportato: {path.suffix}")
        return False
    
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 5000:  # 5GB max
        console.print(f"❌ File troppo grande: {size_mb:.1f}MB (max 5GB)")
        return False
    
    return True

def generate_job_id() -> str:
    """Genera unique job ID"""
    return f"job_{int(datetime.now().timestamp() * 1000)}"

# ============================================================================
# MAIN CLI
# ============================================================================

@click.group()
def cli():
    """🎬 ONWAVE Video Processing CLI v1.0"""
    pass

@cli.command()
def interactive():
    """🎯 Interactive processing workflow (recommended)"""
    
    config = load_config()
    console.clear()
    
    console.print(Panel(
        "[bold cyan]🎬 ONWAVE Video Processing[/bold cyan]\n[dim]Interactive Workflow[/dim]",
        expand=False,
        border_style="cyan"
    ))
    
    # STEP 1: Upload Video
    console.print("\n[bold]STEP 1: Upload Video[/bold]")
    console.print("[dim]Supportati: MP4, MOV, AVI, MKV, WebM[/dim]")
    
    video_path = None
    while not video_path:
        path = Prompt.ask("📁 Percorso video (o .)")
        if path == ".":
            # Show recent files
            console.print("\n[dim]File recenti:[/dim]")
            # TODO: implement file browser
            path = Prompt.ask("📁 Percorso video")
        
        if validate_video(path):
            video_path = path
            file_size = Path(path).stat().st_size / (1024 * 1024)
            console.print(f"✓ Video caricato: {Path(path).name} ({file_size:.1f}MB)")
        else:
            console.print("[yellow]⚠️  Riprova[/yellow]")
    
    # STEP 2: Choose Preset
    console.print("\n[bold]STEP 2: Scegli Preset[/bold]")
    console.print("[dim]Profili pre-configurati per diversi usi[/dim]")
    
    presets = [
        ("social_media", "Social Media (TikTok/Reels/Shorts) - Energico, dinamico, mobile-first"),
        ("educational", "Educational (Tutorial/Corsi) - Chiaro, didattico, con sottotitoli"),
        ("corporate", "Corporate (Branding/Intro) - Professionale, elegante, broadcast-quality"),
        ("testimonial", "Testimonial (Case Study) - Personale, autentico, engagement-focused"),
    ]
    
    for i, (preset_id, preset_desc) in enumerate(presets, 1):
        icon = "→" if preset_id == config['default_preset'] else " "
        console.print(f"  {i}. {icon} [bold]{preset_id}[/bold]\n     {preset_desc}")
    
    preset_choice = Prompt.ask("\nScegli preset", choices=['1', '2', '3', '4'], default='1')
    preset = presets[int(preset_choice) - 1][0]
    console.print(f"✓ Preset selezionato: {preset}")
    
    # STEP 3: Processing Options
    console.print("\n[bold]STEP 3: Opzioni di Processing[/bold]")
    
    remove_silence = Confirm.ask("  Rimuovi silenzi lunghi?", default=True)
    add_subtitles = Confirm.ask("  Genera sottotitoli?", default=True)
    add_voiceover = Confirm.ask("  Aggiungi voiceover sintetizzato?", default=False)
    
    voiceover_text = None
    voiceover_voice = None
    if add_voiceover:
        console.print("\n  [dim]Voice Profiles:[/dim]")
        voices = [
            ("professional", "Neutrale, professionale - Corporate/Formale"),
            ("warm", "Accogliente, amichevole - Tutorial/Storytelling"),
            ("energetic", "Dinamica, entusiasta - Social Media"),
            ("deep", "Profonda, autorevole - Narrazioni/Premium"),
        ]
        for i, (voice_id, voice_desc) in enumerate(voices, 1):
            console.print(f"    {i}. {voice_id} - {voice_desc}")
        
        voice_choice = Prompt.ask("  Scegli voce", choices=['1', '2', '3', '4'], default='1')
        voiceover_voice = voices[int(voice_choice) - 1][0]
        
        console.print("\n  Inserisci testo per voiceover (termina con Ctrl+D):")
        console.print("  [dim]Lascia vuoto per saltare[/dim]")
        try:
            lines = []
            while True:
                line = input("  > ")
                lines.append(line)
            voiceover_text = "\n".join(lines)
        except EOFError:
            voiceover_text = "\n".join(lines) if lines else None
    
    # STEP 4: Output Configuration
    console.print("\n[bold]STEP 4: Output Configuration[/bold]")
    
    output_dir = Prompt.ask(
        "📁 Cartella output",
        default=config['last_output_dir']
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save to config
    config['last_output_dir'] = output_dir
    config['default_preset'] = preset
    save_config(config)
    
    # STEP 5: Cloud Sync (optional)
    console.print("\n[bold]STEP 5: Cloud Sync (Opzionale)[/bold]")
    upload_to_drive = False
    if config['google_drive_enabled']:
        upload_to_drive = Confirm.ask(
            "Carica risultati su Google Drive?",
            default=True
        )
    
    # STEP 6: PROCESSING
    console.print("\n[bold cyan]STEP 6: Processing[/bold cyan]")
    
    job_id = generate_job_id()
    job = VideoJob(
        job_id=job_id,
        video_path=video_path,
        preset=preset,
        status="processing",
        created=datetime.now().isoformat(),
        output_dir=output_dir
    )
    
    jobs = load_jobs()
    jobs[job_id] = job
    save_jobs(jobs)
    
    console.print(f"\n✓ Job creato: {job_id}")
    console.print(f"📺 Video: {Path(video_path).name}")
    console.print(f"📋 Preset: {preset}")
    console.print(f"📁 Output: {output_dir}\n")
    
    # Call backend API to submit job
    import requests
    try:
        response = requests.post(
            f"{config['api_url']}/api/jobs",
            json={
                'job_id': job_id,
                'video_path': video_path,
                'preset': preset,
                'output_dir': output_dir,
                'options': {
                    'remove_silence': remove_silence,
                    'add_subtitles': add_subtitles,
                    'add_voiceover': add_voiceover,
                    'voiceover_text': voiceover_text,
                    'voiceover_voice': voiceover_voice,
                    'upload_to_drive': upload_to_drive
                }
            },
            timeout=10
        )
        
        if response.status_code == 202:
            console.print("[green]✓ Job sottomesso al server[/green]")
            
            # Show real-time progress
            show_progress(job_id, config)
        else:
            console.print(f"[red]❌ Errore server: {response.status_code}[/red]")
            console.print(response.text)
    
    except requests.exceptions.ConnectionError:
        console.print("[yellow]⚠️  Server non raggiungibile. Processing locale...[/yellow]")
        # Fallback: local processing
        process_locally(video_path, preset, output_dir, job)

@cli.command()
def jobs():
    """📋 Visualizza history di job"""
    
    jobs_data = load_jobs()
    
    if not jobs_data:
        console.print("[yellow]Nessun job trovato[/yellow]")
        return
    
    console.print("\n[bold]Recent Jobs[/bold]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Job ID", style="dim")
    table.add_column("Video", style="cyan")
    table.add_column("Preset", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for job_id, job in sorted(jobs_data.items(), key=lambda x: x[1].created, reverse=True)[:20]:
        status_icon = {
            "processing": "🟡",
            "completed": "🟢",
            "error": "🔴",
            "queued": "⚪"
        }.get(job.status, "?")
        
        table.add_row(
            job_id[:8],
            Path(job.video_path).name,
            job.preset,
            f"{status_icon} {job.status}",
            job.created[:10]
        )
    
    console.print(table)

@cli.command()
def config():
    """⚙️  Gestisci configurazione"""
    
    cfg = load_config()
    
    console.print("\n[bold]Configuration[/bold]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value", style="green")
    
    table.add_row("API URL", cfg['api_url'])
    table.add_row("Google Drive", "🟢 Enabled" if cfg['google_drive_enabled'] else "⚪ Disabled")
    table.add_row("Default Preset", cfg['default_preset'])
    table.add_row("Output Dir", cfg['last_output_dir'])
    
    console.print(table)
    
    if Confirm.ask("\n🔧 Modifica configurazione?"):
        if Confirm.ask("Abilita Google Drive?"):
            cfg['google_drive_enabled'] = True
            cfg['google_drive_folder_id'] = Prompt.ask("Google Drive Folder ID")
        
        cfg['api_url'] = Prompt.ask("API URL", default=cfg['api_url'])
        cfg['default_preset'] = Prompt.ask("Default Preset", default=cfg['default_preset'])
        
        save_config(cfg)
        console.print("\n[green]✓ Configurazione salvata[/green]")

@cli.command()
@click.argument('video_path')
@click.option('--preset', default='social_media', help='Preset (social_media, educational, corporate, testimonial)')
@click.option('--output', default=None, help='Output directory')
@click.option('--no-subtitles', is_flag=True, help='Skip subtitle generation')
@click.option('--no-silence', is_flag=True, help='Skip silence removal')
def process(video_path: str, preset: str, output: Optional[str], no_subtitles: bool, no_silence: bool):
    """⚡ Quick processing (non-interactive)"""
    
    if not validate_video(video_path):
        sys.exit(1)
    
    config = load_config()
    if not output:
        output = config['last_output_dir']
    
    Path(output).mkdir(parents=True, exist_ok=True)
    
    job_id = generate_job_id()
    job = VideoJob(
        job_id=job_id,
        video_path=video_path,
        preset=preset,
        status="processing",
        created=datetime.now().isoformat(),
        output_dir=output
    )
    
    jobs = load_jobs()
    jobs[job_id] = job
    save_jobs(jobs)
    
    console.print(f"\n[bold]Processing: {Path(video_path).name}[/bold]")
    console.print(f"Preset: {preset} | Output: {output}\n")
    
    # Submit to API
    import requests
    try:
        response = requests.post(
            f"{config['api_url']}/api/jobs",
            json={
                'job_id': job_id,
                'video_path': video_path,
                'preset': preset,
                'output_dir': output,
                'options': {
                    'remove_silence': not no_silence,
                    'add_subtitles': not no_subtitles,
                    'add_voiceover': False,
                }
            },
            timeout=10
        )
        
        if response.status_code == 202:
            show_progress(job_id, config)
        else:
            console.print(f"[red]Error: {response.status_code}[/red]")
    
    except requests.exceptions.ConnectionError:
        console.print("[yellow]⚠️  API server non disponibile[/yellow]")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def show_progress(job_id: str, config: Dict):
    """Mostra progress in real-time"""
    import requests
    import time
    
    api_url = config['api_url']
    last_step = None
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("[dim]{task.description}[/dim]"),
        expand=True
    ) as progress:
        task = progress.add_task("[cyan]Processing...", total=100)
        
        while True:
            try:
                response = requests.get(f"{api_url}/api/jobs/{job_id}/progress", timeout=5)
                data = response.json()
                
                if data['status'] == 'completed':
                    progress.update(task, completed=100)
                    console.print(f"\n[green]✓ Processing completato![/green]")
                    break
                elif data['status'] == 'error':
                    progress.stop()
                    console.print(f"\n[red]❌ Errore: {data.get('error', 'Unknown error')}[/red]")
                    break
                else:
                    progress.update(
                        task,
                        completed=data['progress'],
                        description=f"[{data.get('current_step', 'processing')}]"
                    )
                    time.sleep(0.5)
            
            except Exception as e:
                time.sleep(1)

def process_locally(video_path: str, preset: str, output_dir: str, job: VideoJob):
    """Fallback: elaborazione locale"""
    console.print("\n[bold]Local Processing[/bold]")
    
    # Call local script
    subprocess.run([
        'python', 'scripts/video-processor.py',
        video_path,
        '--preset', preset,
        '--output', output_dir,
        '--job-id', job.job_id
    ])

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    cli()
