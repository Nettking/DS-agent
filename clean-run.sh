#!/usr/bin/env bash
set -e

echo "🧹 Stopping containers..."
docker compose down

echo "🧼 Removing stopped containers (if any)..."
docker container prune -f >/dev/null 2>&1 || true

echo "🔨 Building images without cache (ui + mvp)..."
docker compose build --no-cache ui mvp

echo "🚀 Starting LocalAI..."
docker compose up -d localai

echo "⏳ Waiting for LocalAI to respond..."
until curl -sf http://localhost:8080/v1/models >/dev/null; do
  sleep 2
done

echo "✅ LocalAI is ready."

echo "🖥️  Starting UI..."
docker compose up -d ui

echo ""
echo "🎉 Done."
echo "➡ UI: http://localhost:8501"
echo "➡ LocalAI: http://localhost:8080"
