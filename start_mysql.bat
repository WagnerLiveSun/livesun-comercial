@echo off
setlocal
cd /d "%~dp0"

:: 1) Detectar Python
set "PYTHON_EXE="
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0.venv313\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv313\Scripts\python.exe"
if not defined PYTHON_EXE (
    echo ERRO: Nenhum ambiente virtual encontrado em .venv ou .venv313.
    echo Crie/ative o ambiente virtual antes de iniciar.
    pause
    exit /b 1
)

:: 2) Configurar banco = MySQL (usa DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME)
echo.
echo [1/2] Banco: MySQL
set "DB_ENGINE=mysql"
set "DB_TYPE=mysql"
set "DB_HOST=localhost"
set "DB_PORT=3306"
set "DB_USER=controller_owner"
set "DB_PASSWORD=Controller@2026!"
set "DB_NAME=comercial"

echo.
echo Inicializando ambiente...
echo Pipeline: DB_ENGINE=mysql | MYSQL local (Hostinger/localhost).
echo Pressione CTRL+C para parar o servidor.

:: 3) Iniciar o app (run.py carrega .env, mas DB_ENGINE fica na memoria do processo)
"%PYTHON_EXE%" run.py
if errorlevel 1 (
    echo.
    echo Erro ao iniciar o programa. Pressione qualquer tecla para fechar...
    pause >nul
    exit /b 1
)
