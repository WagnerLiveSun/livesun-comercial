@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

set "PYTHON_EXE="
if exist "%~dp0.venv313\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv313\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    echo.
    echo Nenhum ambiente virtual encontrado em .venv ou .venv313.
    echo Crie/ative o ambiente antes de iniciar.
    pause
    exit /b 1
)

if /I "%~1"=="validar" goto validar
if /I "%~1"=="testar" goto validar
if /I "%~1"=="run" goto executar

:menu
echo.
echo ==============================================
echo LiveSun Comercial
    echo ==============================================
echo 1 - Iniciar programa
 echo 2 - Rodar validacoes
 echo 3 - Sair
set /p opcao=Escolha uma opcao: 
if "%opcao%"=="1" goto executar
if "%opcao%"=="2" goto validar
if "%opcao%"=="3" exit /b 0
goto menu

:executar
echo Iniciando o programa...
"%PYTHON_EXE%" run.py
if errorlevel 1 (
    echo.
    echo Erro ao iniciar o programa. Pressione qualquer tecla para fechar...
    pause >nul
)
exit /b %errorlevel%

:validar
echo Rodando validacoes...
"%PYTHON_EXE%" -m unittest tests.test_tenant_isolation tests.test_comissoes_importacoes tests.test_conciliacao_permissoes
if errorlevel 1 (
    echo.
    echo Erro nas validacoes. Pressione qualquer tecla para fechar...
    pause >nul
    exit /b %errorlevel%
)
"%PYTHON_EXE%" scripts\validar_comercial.py
if errorlevel 1 (
    echo.
    echo Erro no validador. Pressione qualquer tecla para fechar...
    pause >nul
)
exit /b %errorlevel%
