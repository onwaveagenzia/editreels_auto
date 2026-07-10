FROM python:3.11-slim

# FFmpeg per editing video + font emoji per overlay
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-color-emoji \
    fontconfig \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
# Cartella cache modello Whisper (persistente tra richieste nello stesso container)
ENV HF_HOME=/app/.cache/huggingface

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "900", "--workers", "1", "server:app"]
