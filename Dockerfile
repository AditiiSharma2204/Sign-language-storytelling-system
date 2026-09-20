# ---- build the React UI ----
FROM node:22-alpine AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- runtime: FastAPI serves the API, the media and the built UI ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app backend/app
COPY vocab.txt vocab_wlasl.txt ./
COPY fingerspelling fingerspelling
# Sign clips are not baked into the image (WLASL licence): mount them at runtime, see docker-compose.yml.
COPY --from=ui /ui/dist frontend/dist

# Generated videos are a cache; run as an unprivileged user that owns only that folder.
RUN useradd --create-home app && mkdir -p backend/outputs asl_videos_std asl_videos_wlasl && chown -R app backend/outputs
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
