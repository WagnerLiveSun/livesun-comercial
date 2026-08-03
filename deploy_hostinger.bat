@echo off
REM Script de Deploy para Hostinger via FTP (Windows)
REM Uso: deploy_hostinger.bat

setlocal enabledelayedexpansion

cls
echo.
echo ===================================================
echo  Deploy LiveSun Financeiro para Hostinger
echo ===================================================
echo.

REM Verificar se as variáveis estao definidas
if "%HOSTINGER_FTP_SERVER%"=="" (
    echo ERRO: Configure as variaveis de ambiente:
    echo.
    echo  set HOSTINGER_FTP_SERVER=seu-servidor.hostinger.com
    echo  set HOSTINGER_FTP_USER=seu-usuario
    echo  set HOSTINGER_FTP_PASSWORD=sua-senha
    echo.
    echo Ou edite este script com seus dados
    pause
    exit /b 1
)

echo Informacoes de Deploy:
echo  FTP Server: %HOSTINGER_FTP_SERVER%
echo  FTP User: %HOSTINGER_FTP_USER%
echo.

REM Criar arquivo FTP temporario
setlocal
set "TEMP_FTP=%temp%\ftp_commands.txt"

(
    echo open %HOSTINGER_FTP_SERVER%
    echo %HOSTINGER_FTP_USER%
    echo %HOSTINGER_FTP_PASSWORD%
    echo cd public_html
    echo.
    echo REM Upload de arquivos
    echo put requirements.txt
    echo put run.py
    echo put setup_db.py
    echo put migrate_comissoes.py
    echo put .env
    echo.
    echo REM Upload de diretorio src (se suportado)
    echo lcd src
    echo cd src
    echo mput *
    echo cd ..
    echo lcd ..
    echo.
    echo REM Upload de config
    echo lcd config
    echo cd config
    echo mput *
    echo cd ..
    echo lcd ..
    echo.
    echo REM Upload de migrations
    echo lcd migrations
    echo cd migrations
    echo mput *
    echo cd ..
    echo lcd ..
    echo.
    echo REM Verificar
    echo ls
    echo quit
) > "%TEMP_FTP%"

echo [1/4] Conectando ao FTP...
echo.

REM Executar FTP
ftp -s:"%TEMP_FTP%"

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo  Upload via FTP concluido com sucesso!
    echo ===================================================
    echo.
) else (
    echo.
    echo ERRO: Falha no upload via FTP
    echo Verifique suas credenciais
    echo.
    del "%TEMP_FTP%"
    pause
    exit /b 1
)

REM Limpar arquivo temporario
del "%TEMP_FTP%"

echo [2/4] Deploy iniciado!
echo.
echo PROXIMOS PASSOS:
echo.
echo 1. Acesse seu cPanel
echo 2. Vá para: Setup Python App
echo 3. Configure se ainda nao tiver feito
echo 4. Acesse: https://seu-dominio.com
echo 5. Faça login com: admin / admin123
echo.
echo PARA INICIALIZAR O BANCO:
echo.
echo 1. No cPanel, vá para MySQL Databases
echo 2. Abra phpMyAdmin
echo 3. Selecione seu banco de dados
echo 4. Clique em SQL
echo 5. Cole o conteudo de: initialize_db_hostinger.sql
echo 6. Execute
echo.
echo Nao esqueça de:
echo  - Alterar a senha do admin imediatamente
echo  - Configurar aliquota de comissao em /comissoes/parametros
echo.
pause
