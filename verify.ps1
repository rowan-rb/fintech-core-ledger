Write-Host "Iniciando verificación del Core Ledger..." -ForegroundColor Cyan

Write-Host "`n[1] Comprobando contenedores..." -ForegroundColor Yellow
docker compose ps

Write-Host "`n[2] Inicializando Base de Datos..." -ForegroundColor Yellow
python scripts/init_db.py

Write-Host "`n[3] Ejecutando suite de tests (Caos, Particionamiento, Idempotencia)..." -ForegroundColor Yellow
pytest tests/ -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nTODO OK: El sistema es resiliente, auditable y rastrea fallos." -ForegroundColor Green
} else {
    Write-Host "`nFALLOS DETECTADOS: Revisa los tests." -ForegroundColor Red
}
