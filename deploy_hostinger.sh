#!/bin/bash
# Script de Deploy para Hostinger via FTP
# Uso: bash deploy_hostinger.sh

set -e  # Parar se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════╗"
echo "║  Deploy LiveSun Financeiro para Hostinger      ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar se variáveis estão definidas
if [ -z "$HOSTINGER_FTP_SERVER" ] || [ -z "$HOSTINGER_FTP_USER" ] || [ -z "$HOSTINGER_FTP_PASSWORD" ]; then
    echo -e "${RED}✗ Erro: Configure as variáveis de ambiente:${NC}"
    echo "  export HOSTINGER_FTP_SERVER=seu-servidor.hostinger.com"
    echo "  export HOSTINGER_FTP_USER=seu-usuario"
    echo "  export HOSTINGER_FTP_PASSWORD=sua-senha"
    exit 1
fi

# Ou usar arquivo .env para Hostinger
HOSTINGER_FTP_SERVER="${HOSTINGER_FTP_SERVER:-.env}"
HOSTINGER_FTP_USER="${HOSTINGER_FTP_USER:-.env}"
HOSTINGER_FTP_PASSWORD="${HOSTINGER_FTP_PASSWORD:-.env}"

echo -e "${YELLOW}Informações de Deploy:${NC}"
echo "  FTP Server: $HOSTINGER_FTP_SERVER"
echo "  FTP User: $HOSTINGER_FTP_USER"
echo ""

# Criar arquivo de script FTP
FTP_SCRIPT=$(mktemp)

cat > "$FTP_SCRIPT" << EOF
open $HOSTINGER_FTP_SERVER
$HOSTINGER_FTP_USER
$HOSTINGER_FTP_PASSWORD

cd public_html

# Upload de arquivos Python
put requirements.txt
put run.py
put setup_db.py
put migrate_comissoes.py
put .env

# Upload de diretórios
mput src/*
mput config/*
mput migrations/*

# Listar arquivos para confirmar
ls

quit
EOF

echo -e "${YELLOW}[1/4] Conectando ao FTP...${NC}"
ftp -n < "$FTP_SCRIPT"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Upload via FTP concluído!${NC}"
else
    echo -e "${RED}✗ Erro no upload FTP${NC}"
    rm "$FTP_SCRIPT"
    exit 1
fi

rm "$FTP_SCRIPT"

echo -e "${YELLOW}[2/4] Deploy concluído!${NC}"
echo ""
echo -e "${GREEN}Próximos passos:${NC}"
echo "1. Acesse cPanel → Setup Python App"
echo "2. Configure se ainda não tiver feito"
echo "3. Acesse: https://seu-dominio.com"
echo "4. Faça login com admin/admin123"
echo "5. Configure alíquota padrão em /comissoes/parametros"
echo ""
echo -e "${YELLOW}Para inicializar o banco no cPanel:${NC}"
echo "1. Vá para MySQL Databases"
echo "2. Abra phpMyAdmin"
echo "3. Cole o SQL de: initialize_db_hostinger.sql"
echo ""
echo -e "${GREEN}✓ Deploy iniciado com sucesso!${NC}"
