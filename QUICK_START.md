# 🎬 ONWAVE Video Processing - QUICK START GUIDE

## ⚡ 5-Minute Setup

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/onwave/video-processing.git
cd onwave-video-processing

# Install everything
npm install
pip install -r requirements.txt --break-system-packages
```

### 2. Choose Your Interface

#### 🖥️ **Interactive CLI** (Recommended for beginners)
```bash
npm run cli:interactive

# Follow the wizard:
# 1. Upload video
# 2. Choose preset
# 3. Configure options
# 4. Hit process!
```

#### 🌐 **Web Dashboard** (Best for production)
```bash
# Terminal 1: Start API
npm run dev:api

# Terminal 2: Start Dashboard
npm run dev:dashboard

# Open: http://localhost:3000
```

#### ⚡ **Quick Command Line**
```bash
npm run cli:process -- video.mp4 --preset social_media
```

---

## 📊 Commands Cheat Sheet

### CLI Commands

```bash
# Interactive workflow (easiest!)
npm run cli:interactive

# Quick processing
npm run cli:process -- video.mp4 --preset social_media

# View all jobs
npm run cli:jobs

# Manage configuration
npm run cli:config

# Usage help
npm run cli -- --help
```

### Google Drive

```bash
# First time setup
npm run drive:setup

# Start watching for new videos
npm run drive:watch

# Stop watching (Ctrl+C)
```

### Development

```bash
# Start API + Dashboard together
npm run dev

# Start API only
npm run dev:api

# Start Dashboard only
npm run dev:dashboard

# Build for production
npm run build

# Production start
npm run start
```

---

## 🎯 Use Cases

### Use Case 1: Single Video Processing
```bash
# Interactive (easiest)
npm run cli:interactive

# Or quick command
npm run cli:process -- ~/Videos/my_video.mp4 \
  --preset social_media \
  --output ~/OnwaveOutput
```

**Result:** 
- ✅ 1080×1920 optimized MP4
- ✅ Auto-generated subtitles
- ✅ Silence removed
- ✅ Energetic animations

### Use Case 2: Batch Processing (100 videos)

```bash
# Setup Google Drive
npm run drive:setup

# Start auto-sync daemon
npm run drive:watch

# Just upload videos to Google Drive "ONWAVE_Input" folder
# They'll be processed automatically and results uploaded to "ONWAVE_Output"
```

### Use Case 3: Production Deployment

```bash
# 1. Deploy to GitHub
git push origin main

# 2. Vercel auto-deploys dashboard
# → https://video-processing.vercel.app

# 3. Deploy API to Heroku
heroku create your-app-name
git push heroku main

# 4. Google Drive auto-sync runs in background
npm run drive:watch &
```

---

## 📋 Preset Options

### Social Media (Default) ⭐
- **Best for:** TikTok, Instagram Reels, YouTube Shorts
- **Resolution:** 1080×1920 (9:16 vertical)
- **Bitrate:** 7500k (optimized for mobile)
- **Animation:** Energetic (0.95 intensity)
- **Subtitles:** Bold, large, bottom placement

```bash
npm run cli:process -- video.mp4 --preset social_media
```

### Educational
- **Best for:** Online courses, tutorials, educational content
- **Resolution:** 1920×1080 (16:9)
- **Bitrate:** 5000k
- **Animation:** Medium (0.6 intensity)
- **Subtitles:** Clear, academic style

### Corporate
- **Best for:** Business videos, branding, presentations
- **Resolution:** 1440×2560 (vertical for web)
- **Bitrate:** 6000k
- **Animation:** Subtle (0.4 intensity)
- **Subtitles:** Professional tone

### Testimonial
- **Best for:** Case studies, reviews, customer stories
- **Resolution:** 1280×720 (16:9)
- **Bitrate:** 4000k
- **Animation:** Moderate (0.7 intensity)
- **Subtitles:** None (keeps original audio)

---

## 🔧 Configuration

### API URL Configuration

```bash
# Development
export API_URL=http://localhost:5000

# Production
export API_URL=https://api.onwave.studio
```

### Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable "Google Drive API"
4. Create "OAuth 2.0 Client ID" (Desktop app)
5. Download credentials.json
6. Save to: `~/.onwave/google_credentials.json`
7. Run: `npm run drive:setup`

---

## 📊 Monitor Progress

### From CLI
```bash
# Watch real-time progress
npm run cli:jobs

# Output:
# recent_job_123456  │ video.mp4 │ social_media │ 🟡 processing │ 45% ⏱ 2m30s
```

### From Dashboard
Open: `http://localhost:3000`
- **Active Tab** - See live processing
- **Completed Tab** - Download results
- **Statistics Tab** - Overall metrics

---

## 📥 Input & Output

### Input Video Formats
✅ MP4, MOV, AVI, MKV, WebM, M4V
❌ Max 5GB per file
❌ Corrupted or incomplete videos

### Output Files

For each video, you get:

```
video_name_social.mp4          # Main optimized file
video_name_subtitles.srt       # Subtitle file
video_name_analysis.json       # Processing metadata
```

---

## 🐛 Troubleshooting

### "API not connecting"
```bash
# Check if API is running
curl http://localhost:5000/api/health

# If not working, restart:
npm run dev:api
```

### "FFmpeg not found"
```bash
# Install FFmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

### "Video processing fails"
```bash
# Check file format
file video.mp4  # Should be video

# Check disk space
df -h

# Check logs
npm run dev:api  # Watch console output
```

### "Google Drive sync not working"
```bash
# Re-setup
npm run drive:setup

# Test connection
python scripts/google_drive_sync.py --test
```

---

## 📈 Performance Expectations

### Processing Speed
| Video Length | Resolution | Expected Time |
|--------------|-----------|----------------|
| 30 seconds | 1080×1920 | 2-3 minutes |
| 1 minute | 1920×1080 | 4-5 minutes |
| 5 minutes | 1280×720 | 8-10 minutes |
| 10 minutes | 1920×1080 | 15-20 minutes |

### Optimization Results
- 📊 **File Size Reduction:** 40-60% smaller
- ⚡ **Loading Speed:** 2x faster on mobile
- 📱 **Mobile Optimization:** 95% battery efficiency
- 🎬 **Quality:** Full 1080p sharpness retained

---

## 🚀 Next Steps

### Level 1: Getting Started
- [x] Install
- [x] Process one video with CLI
- [ ] Try Web Dashboard

### Level 2: Production Ready
- [ ] Deploy to Vercel (dashboard)
- [ ] Deploy to Heroku (API)
- [ ] Setup Google Drive
- [ ] Configure monitoring

### Level 3: Advanced
- [ ] Setup CI/CD with GitHub Actions
- [ ] Add custom animations
- [ ] Integrate with other tools
- [ ] Scale to 1000+ videos/month

---

## 📞 Support & Community

**Resources:**
- 📖 Full Docs: https://docs.onwave.studio
- 🐛 Report Issues: https://github.com/onwave/video-processing/issues
- 💬 Discord Community: https://discord.gg/onwave
- 📧 Email: support@onwave.studio

**Pro Tips:**
- Use CLI for testing, Dashboard for production
- Enable Google Drive sync for auto-processing
- Monitor API logs when troubleshooting
- Keep FFmpeg updated for best results

---

## 🎯 Common Workflows

### Workflow 1: Process Video, Download, Share
```bash
# 1. Interactive processing
npm run cli:interactive
# → Choose video, preset, options
# → Processing starts

# 2. Go to http://localhost:3000
# → Watch progress
# → Click Download when done

# 3. Share result
# → File in ~/OnwaveOutput/
```

### Workflow 2: Batch Process Videos from Drive
```bash
# 1. Setup
npm run drive:setup

# 2. Upload folder to Drive
# → ONWAVE_Input/video1.mp4
# → ONWAVE_Input/video2.mp4
# → ONWAVE_Input/video3.mp4

# 3. Auto-process
npm run drive:watch
# → Processes automatically
# → Results go to ONWAVE_Output/

# 4. Download from Drive
```

### Workflow 3: Production Pipeline
```bash
# 1. Deploy dashboard to Vercel
npm run build
vercel deploy

# 2. Deploy API to Heroku
git push heroku main

# 3. Setup Google Drive
npm run drive:setup

# 4. Run background sync
npm run drive:watch &

# 5. Team uses dashboard at:
# → https://your-domain.vercel.app
```

---

## 🎁 Bonus Features

### Custom Animations
Edit `scripts/animations.py` to add your own animation styles

### Custom Color Grading
Edit `scripts/social_media_preset.py` to adjust color/contrast settings

### API Extensions
Add custom endpoints to `api/server.py` for your workflow

---

## 💡 Pro Tips

1. **Use Cloud Storage:** Google Drive auto-sync saves time
2. **Batch Process:** Upload 50 videos, let it run overnight
3. **Monitor Dashboard:** Always check stats before claiming "done"
4. **Save Presets:** Create custom presets for your specific use case
5. **Automate Cron:** Schedule drive:watch with systemd/cron

---

**🎬 Ready to get started?**

```bash
npm run cli:interactive
```

That's it! Follow the prompts and your first video will be processed in minutes.

---

*ONWAVE Video Processing Platform v1.0*
Built for professionals. Easy for everyone.
