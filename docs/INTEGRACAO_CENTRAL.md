# Assinatura LiveSun administrada no Central

Consulte `D:\App_LiveSun\LiveSun_CentralControle\livesun-central\docs\COMERCIAL_CENTRAL.md` para o fluxo completo de migração.

- Produto: COMERCIAL; módulos e permissões continuam neste sistema.
- Tela de configuração: `/backoffice/comercial/central/`, exige as mesmas credenciais/autorização do backoffice.
- Tabelas novas: aplicar `migrations/mysql/038_central_assinaturas.sql` ou `migrations/postgresql/038_central_assinaturas.sql` com o owner do banco; são aditivas e não incluem segredos.
- Não habilita sozinho: exige preencher configuração, criar vínculos, conferir importação e confirmar CENTRAL.
- Credenciais ficam criptografadas no banco do próprio Comercial. Pode configurar `CENTRAL_ENCRYPTION_KEY` (Fernet) como chave-mestra exclusiva; na ausência usa derivação da SECRET_KEY. Preserve essa chave nos deploys; trocá-la sem recriptografia torna a configuração ilegível.
- O produto não cria recorrências de assinatura no Asaas quando o Central está ativo. O antigo webhook `/webhooks/asaas` de assinatura responde 410 após virada.
- **Nenhum arquivo de serviço/rota dos boletos operacionais Asaas/Inter foi alterado.** As cobranças dos clientes continuam funcionando no Comercial.
- Eventos HMAC em `/webhooks/assinatura`, estado assinado em `/central/estado/{cliente_id}` e purga autorizada em `/central/purgar`.
- Integração não promove administrador comum a operador de plataforma; login/RBAC e autorização de módulos permanecem locais.
- Purga remove dados do tenant alvo somente no banco deste produto, sem tocar Central ou Propostas; exige EXCLUIDA e retenção ou antecipação assinada.
- Não execute purga em produção sem ensaio em cópia descartável de banco completo e inventário de anexos. Arquivos fora do banco não são removidos automaticamente nesta etapa.
- Não reutilize porta 5000 se Propostas também estiver rodando: utilize, por exemplo, Comercial 5002, Propostas 5000 e Central 5001.

As novas tabelas têm DDL versionado; não é necessário modificar credenciais bancárias ou ler arquivos de certificados para instalar.

## Página de atendimento para acesso restrito (somente local)

Restrições comerciais do Central são exibidas em `src/templates/errors/commercial_access.html`, com o tema atual do Comercial e CSS isolado em `src/static/css/commercial-access.css`. Mantém HTTP 403 para bloqueio e 503 para indisponibilidade temporária; não libera acesso nem muda status de assinatura, bonificações, módulos ou cobranças Asaas/Inter. Requisições JSON continuam recebendo JSON e erros de autorização não comerciais não são substituídos.

Contatos: suporte@livesun.com.br, telefone 71 99999-0204 e botão para `https://app.pipefy.com/public/form/ETeM9Gbz`, em nova aba. A página não mostra menus operacionais; permite voltar ao login/sair e verificar acesso novamente. A rota pública de suporte fica disponível durante restrições do Central.

Alterações preparadas apenas na estação, sem push/deploy ou migrations executadas. Testes isolados: `python -m pytest tests/test_commercial_access_page.py tests/test_central_assinatura_separation.py tests/test_central_env.py tests/test_central_theme.py -q`.