Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  CRM GLOBAL CARDS + BLING - Inicializacao Local (127.0.0.1)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "[1/2] Iniciando Backend FastAPI + GlobalCardsDBFEngine em http://127.0.0.1:8765 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\backend'; python run.py"

Write-Host "[2/2] Iniciando Frontend React + Vite em http://127.0.0.1:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\frontend'; npm run dev"

Write-Host "Aplicacao iniciada! Acesse http://127.0.0.1:5173 no navegador." -ForegroundColor Yellow
