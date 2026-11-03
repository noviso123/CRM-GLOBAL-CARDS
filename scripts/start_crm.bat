@echo off
title CRM GLOBAL CARDS - Inicializacao Local
echo =====================================================
echo   CRM GLOBAL CARDS + BLING - Inicializacao Local
echo =====================================================
echo.
cd /d "%~dp0.."

echo [1/2] Iniciando Backend FastAPI (Porta 8765)...
start "CRM Global Cards - Backend" cmd /k "cd backend && python run.py"

echo [2/2] Iniciando Frontend React + Vite (Porta 5173)...
start "CRM Global Cards - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =====================================================
echo   CRM GLOBAL CARDS iniciado com sucesso!
echo   Acesse: http://127.0.0.1:5173
echo   Usuario Admin: admin (ou admin@globalcards.com.br)
echo   Senha Admin:   GlobalCards@2026
echo =====================================================
echo.
pause

