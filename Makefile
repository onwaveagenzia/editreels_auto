.PHONY: help install dev-setup dev-backend dev-dashboard deploy-vercel deploy-heroku clean lint test

# Colors
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m # No Color

help:
	@echo "$(BLUE)🎬 ONWAVE Video Processing Suite - Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install           Install all dependencies"
	@echo "  make dev-setup         Setup development environment"
	@echo "  make dev-backend       Run backend API (Flask)"
	@echo "  make dev-dashboard     Run frontend dashboard (Next.js)"
	@echo "  make dev-cli           Run interactive CLI"
	@echo ""
	@echo "$(GREEN)Production:$(NC)"
	@echo "  make deploy-vercel     Deploy dashboard to Vercel"
	@echo "  make deploy-heroku     Deploy backend to Heroku"
	@echo "  make deploy-railway    Deploy backend to Railway"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make lint              Run linters"
	@echo "  make test              Run tests"
	@echo "  make clean             Clean temp files and caches"
	@echo "  make format            Format code (black)"
	@echo ""

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install --break-system-packages -r requirements.txt
	cd dashboard && npm install
	@echo "$(GREEN)✓ Installation complete$(NC)"

dev-setup:
	@echo "$(BLUE)Setting up development environment...$(NC)"
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env
	@echo "$(YELLOW)⚠️  Edit .env with your configuration$(NC)"
	@echo "$(GREEN)✓ Setup complete$(NC)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev-backend:
	@echo "$(BLUE)Starting backend API on http://localhost:5000$(NC)"
	python api/server.py

dev-dashboard:
	@echo "$(BLUE)Starting dashboard on http://localhost:3000$(NC)"
	cd dashboard && npm run dev

dev-cli:
	@echo "$(BLUE)Starting interactive CLI$(NC)"
	python scripts/cli.py interactive

dev-all:
	@echo "$(BLUE)Starting all services...$(NC)"
	@echo "Dashboard: http://localhost:3000"
	@echo "API: http://localhost:5000"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  make dev-backend"
	@echo "  make dev-dashboard"

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-vercel:
	@echo "$(BLUE)Deploying to Vercel...$(NC)"
	npm i -g vercel
	vercel --prod
	@echo "$(GREEN)✓ Deployed to Vercel$(NC)"

deploy-vercel-preview:
	@echo "$(BLUE)Creating Vercel preview deployment...$(NC)"
	vercel
	@echo "$(GREEN)✓ Preview deployed$(NC)"

deploy-heroku:
	@echo "$(BLUE)Deploying backend to Heroku...$(NC)"
	heroku login
	heroku create onwave-api || true
	heroku config:set ELEVENLABS_API_KEY=$$ELEVENLABS_API_KEY
	git push heroku main
	@echo "$(GREEN)✓ Deployed to Heroku$(NC)"

deploy-railway:
	@echo "$(BLUE)Deploying backend to Railway...$(NC)"
	railway up
	@echo "$(GREEN)✓ Deployed to Railway$(NC)"

deploy-docker:
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t onwave-api .
	docker run -p 5000:5000 onwave-api
	@echo "$(GREEN)✓ Docker image running$(NC)"

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 scripts/ api/ --max-line-length=120
	black scripts/ api/ --check
	cd dashboard && npm run lint
	@echo "$(GREEN)✓ Linting complete$(NC)"

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	black scripts/ api/
	cd dashboard && npm run format || true
	@echo "$(GREEN)✓ Code formatted$(NC)"

test:
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

# ============================================================================
# MAINTENANCE
# ============================================================================

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info .coverage htmlcov .next
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

logs-api:
	@echo "$(BLUE)Backend logs:$(NC)"
	tail -f ~/.onwave/logs/api.log 2>/dev/null || echo "No logs yet"

logs-sync:
	@echo "$(BLUE)Google Drive sync logs:$(NC)"
	tail -f ~/.onwave/logs/sync.log 2>/dev/null || echo "No logs yet"

status:
	@echo "$(BLUE)Service Status:$(NC)"
	@curl -s http://localhost:5000/api/health 2>/dev/null && echo "✓ API: OK" || echo "✗ API: Not running"
	@curl -s http://localhost:3000 2>/dev/null && echo "✓ Dashboard: OK" || echo "✗ Dashboard: Not running"

# ============================================================================
# GOOGLE DRIVE
# ============================================================================

drive-setup:
	@echo "$(BLUE)Setting up Google Drive integration...$(NC)"
	python scripts/google_drive_sync.py setup

drive-watch:
	@echo "$(BLUE)Starting Google Drive watcher...$(NC)"
	python scripts/google_drive_sync.py watch

# ============================================================================
# PRESET & CONFIG
# ============================================================================

show-preset-social:
	@echo "$(BLUE)Social Media Preset Configuration:$(NC)"
	python scripts/preset_social_media.py show

export-preset-social:
	@echo "$(BLUE)Exporting Social Media Preset...$(NC)"
	python scripts/preset_social_media.py export /tmp/social_media_preset.json
	@echo "$(GREEN)✓ Exported to /tmp/social_media_preset.json$(NC)"

# ============================================================================
# GIT & GITHUB
# ============================================================================

git-init:
	@echo "$(BLUE)Initializing Git repo...$(NC)"
	git init
	git add .
	git commit -m "Initial commit: ONWAVE Video Skill v1.0"
	@echo "$(YELLOW)Next: Set remote and push$(NC)"
	@echo "  git remote add origin <URL>"
	@echo "  git push -u origin main"

git-push:
	@echo "$(BLUE)Pushing to GitHub...$(NC)"
	git push origin main
	@echo "$(GREEN)✓ Pushed$(NC)"

git-pull:
	@echo "$(BLUE)Pulling from GitHub...$(NC)"
	git pull origin main
	@echo "$(GREEN)✓ Pulled$(NC)"

# ============================================================================
# QUICK START
# ============================================================================

quick-start: install
	@echo ""
	@echo "$(GREEN)🎬 ONWAVE Quick Start Complete!$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Edit .env with your API keys"
	@echo "  2. Run backend:   make dev-backend"
	@echo "  3. Run dashboard: make dev-dashboard"
	@echo "  4. Run CLI:       make dev-cli"
	@echo ""
	@echo "Visit:"
	@echo "  Dashboard: http://localhost:3000"
	@echo "  API Docs:  http://localhost:5000/api/health"
	@echo ""

# ============================================================================
# DEFAULT
# ============================================================================

.DEFAULT_GOAL := help
