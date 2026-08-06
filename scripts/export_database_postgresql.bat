@echo off
REM Script de exportação do banco de dados PostgreSQL local
REM Uso: export_database_postgresql.bat

echo Exportando banco de dados PostgreSQL local...
echo.

REM Configurações (altere conforme necessário)
set DB_HOST=localhost
set DB_PORT=5432
set DB_USER=postgres
set DB_PASSWORD=
set DB_NAME=comercial
set OUTPUT_DIR=backup

REM Criar diretório de backup se não existir
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Gerar nome do arquivo com data e hora
set TIMESTAMP=%date:~0,2%%date:~3,2%%date:~6,4%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%OUTPUT_DIR%\postgresql_backup_%TIMESTAMP%.sql

REM Definir senha como variável de ambiente
set PGPASSWORD=%DB_PASSWORD%

REM Exportar banco
pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% %DB_NAME% > "%OUTPUT_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Backup realizado com sucesso!
    echo Arquivo: %OUTPUT_FILE%
) else (
    echo.
    echo Erro ao realizar backup!
    echo Verifique as credenciais do banco de dados.
)

REM Limpar variável de ambiente
set PGPASSWORD=

pause
