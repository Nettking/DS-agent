Write-Host "Stopping containers..."
docker compose down

Write-Host "Removing stopped containers..."
docker container prune -f | Out-Null

Write-Host "Building images without cache (ui + mvp)..."
docker compose build --no-cache ui mvp

Write-Host "Starting LocalAI..."
docker compose up -d localai

Write-Host "Waiting for LocalAI to respond..."
while ($true) {
    try {
        $r = Invoke-WebRequest -Uri http://localhost:8080/v1/models -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    Start-Sleep -Seconds 2
}

Write-Host "LocalAI is ready."

Write-Host "Starting UI..."
docker compose up -d ui

Write-Host ""
Write-Host "Done."
Write-Host "➡ UI: http://localhost:8501"
Write-Host "➡ LocalAI: http://localhost:8080"
