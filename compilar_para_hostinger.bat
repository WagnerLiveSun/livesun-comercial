@echo off
REM Script para preparar arquivos para deploy no Hostinger

REM Limpa pasta de build anterior
if exist dist rmdir /s /q dist
mkdir dist
mkdir dist\src
mkdir dist\config
mkdir dist\data
mkdir dist\uploads

REM Copia arquivos principais
xcopy /E /I /Y src dist\src
xcopy /E /I /Y config dist\config
xcopy /E /I /Y data dist\data
xcopy /E /I /Y uploads dist\uploads
copy /Y requirements.txt dist\requirements.txt
copy /Y run.py dist\run.py
copy /Y setup.cfg dist\setup.cfg
copy /Y iniciar.bat dist\iniciar.bat
copy /Y iniciar.sh dist\iniciar.sh
copy /Y README.md dist\README.md
copy /Y QUICK_START.md dist\QUICK_START.md
copy /Y criar_banco_hostinger.sql dist\criar_banco_hostinger.sql

REM Remove arquivos de cache Python
for /r dist %%f in (__pycache__) do rmdir /s /q "%%f"

REM Mensagem final
echo Deploy pronto na pasta dist. Faça upload do conteúdo da pasta dist para o Hostinger.
pause
