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

:: 2) Configurar banco = PostgreSQL
:: Senha preenchida a partir de CriaPostgreeSQL_MontuDB/01_recriar_database_roles_schemas.sql.
echo.
echo [1/2] Banco: PostgreSQL
echo [1/2] Host: 127.0.0.1:55432 (SSH tunnel do Postgres local)
set "DB_ENGINE=postgres"
set "POSTGRES_HOST=127.0.0.1"
set "POSTGRES_PORT=55432"
set "POSTGRES_DATABASE=comercial"
set "POSTGRES_USER=livesun_api"
set "POSTGRES_PASSWORD=LiveSun@2017!@@"
set "DB_TYPE=postgres"

echo.
echo Inicializando ambiente...
echo Pipeline: DB_ENGINE=postgres, Postgres (RLS ativo por padrao).
echo NOTA: POSTGRES_USER nao pode ser postgres/comercial_db_owner/livesun_etl.
echo Pressione CTRL+C para parar o servidor.

:: 3) Iniciar o app (run.py carrega .env, mas DB_ENGINE ja fica na memoria do processo)
"%PYTHON_EXE%" run.py
if errorlevel 1 (
    echo.
    echo Erro ao iniciar o programa. Pressione qualquer tecla para fechar...
    pause >nul
    exit /b 1
)
