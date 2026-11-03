@echo off
title CRM GLOBAL CARDS - Inicializacao Local
echo ======================================================================
echo             CRM GLOBAL CARDS + BLING - INICIALIZACAO LOCAL
echo ======================================================================
echo.
cd /d "%~dp0"

echo [1/2] Iniciando Servidor Backend FastAPI (127.0.0.1:8765)...
start "CRM Global Cards - Backend (8765)" cmd /k "cd backend && python run.py"

echo [2/2] Iniciando Servidor Frontend React Vite (127.0.0.1:5173)...
start "CRM Global Cards - Frontend (5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo   CRM GLOBAL CARDS iniciado com sucesso!
echo.
echo   URL no Navegador: http://127.0.0.1:5173
echo   Usuario Admin:    admin (ou admin@globalcards.com.br)
echo   Senha Admin:      GlobalCards@2026
echo ======================================================================
echo.
pause

