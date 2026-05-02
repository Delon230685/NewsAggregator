# start_all.ps1
Write-Host "Starting all services..." -ForegroundColor Green

# Запускаем Redis если не запущен
$redisRunning = docker ps | findstr redis
if (-not $redisRunning) {
    Write-Host "Starting Redis..." -ForegroundColor Yellow
    docker start redis 2>$null
    if ($LASTEXITCODE -ne 0) {
        docker run -d -p 6379:6379 --name redis redis
    }
}

# Запускаем FastAPI
Write-Host "Starting FastAPI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 3

# Запускаем Celery worker
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; celery -A app.tasks worker --loglevel=info --pool=solo"

Start-Sleep -Seconds 2

# Запускаем Celery beat
Write-Host "Starting Celery beat..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\Activate; celery -A app.tasks beat --loglevel=info"

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "📚 Swagger UI: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🐳 Redis: localhost:6379" -ForegroundColor Cyan
