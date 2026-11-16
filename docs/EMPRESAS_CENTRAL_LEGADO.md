# Descoberta do Comercial no Central

O procedimento e descrito em:
`D:\App_LiveSun\LiveSun_CentralControle\livesun-central\docs\EMPRESAS_COMERCIAL.md`.

- Banco do Comercial permanece MySQL da Hostinger, sem conexao direta pelo Central.
- Novas rotas GET `/central/empresas` e `/central/empresas/<id>` exigem HMAC valido
  mesmo com controle desativado. A assinatura inclui a query string da listagem.
- Callback legado permite preparar vinculos antes da ativacao, conferindo documento,
  evento, hash da origem, plano, situacao, bonificacao e validade do estado recebido.
- A preparacao nao muda assinatura legada, plano/limites locais, cobrancas ou acesso.
- Reutiliza tabelas MySQL 038/039 existentes; nao requer nova migration.
- Publicar Comercial antes do novo menu Empresas do Comercial no Central.
- Nao ativar `CENTRAL_ENABLED` ate conferir todos os vinculos. Purga permanece separada.
- Esta implementacao foi validada localmente; nenhum deploy ou dado real migrado.