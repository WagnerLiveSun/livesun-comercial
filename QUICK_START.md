# Guia Rápido - LiveSun Comercial

## Iniciar no Windows
1. Abra o terminal na pasta do projeto.
2. Execute `iniciar_comercial.bat`.
3. Acesse `http://localhost:5000`.
4. Login padrão: `admin` / `admin123`.

## Iniciar manualmente
```bash
python run.py
```

## Banco de dados
- Configure `.env` com `DB_NAME=comercial`.
- Se precisar criar do zero, use `criar_banco.sql` ou `schema_comercial.sql` conforme o objetivo.

## Observação
Este guia cobre apenas o fluxo rápido atual. Detalhes de operação ficam em [MANUAL_COMERCIAL.md](MANUAL_COMERCIAL.md) e [DOCUMENTACAO.md](DOCUMENTACAO.md).
