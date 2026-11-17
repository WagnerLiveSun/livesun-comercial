# Publicacao controlada do Comercial com receptor Central

## Escopo

- O Comercial continua usando o MySQL da Hostinger. Nao migrar para PostgreSQL.
- Publicar o receptor nao equivale a ativar o controle de assinaturas pelo Central.
- Nao alterar credenciais, certificados ou rotinas de cobranca bancaria operacional.
- Os ajustes de navegacao e manutencao de Lancamentos fazem parte desta revisao.

## Preparacao

1. Guardar backup separado do MySQL de producao e dos arquivos persistentes.
2. Aplicar somente os incrementais MySQL `038_central_assinaturas.sql` e
   `039_central_autocadastro.sql`, conferindo a estrutura de tabelas preexistentes.
3. Preservar as variaveis atuais de conexao MySQL e a `SECRET_KEY` do Comercial.
4. Manter a integracao desativada durante a publicacao. Por padrao, sem registro
   ativo em `central_config_comercial` e sem `CENTRAL_ENABLED=true`, nao ha ativacao.
5. Nao publicar arquivos `.env`, certificados, dumps, backups ou segredos.

## Publicacao e conferencia

- Em 17/11/2026, por solicitacao do responsavel, os arquivos de deploy do Render
  foram restaurados a versao anterior ao commit `1436aa2`: push na `main`
  volta a acionar o workflow e `render.yaml` volta a declarar `autoDeploy: true`.
  Esse fluxo legado nao depende do secret `RENDER_DEPLOY_HOOK_URL`.
- Os jobs legados Railway/FTP estao desativados para evitar publicacoes paralelas.
- Render continua usando MySQL; conferir no painel qual commit entrou em producao.
- Conferir `/auth/login` e a tela `/backoffice/comercial/central/` com usuario
  autorizado ao backoffice. A rota exige autenticacao e autorizacao adicional.
- Conferir lancamentos: oito colunas, sem Conta Fluxo, sem botoes fixos sobre linhas.
- A alteracao dos nomes dos cookies exige novo login dos usuarios.
- Testar cadastro legado com Central desativado antes de autorizar a ativacao.

## Ativacao posterior

Preferir uma unica fonte de configuracao. Pela tela do backoffice, deixar a
variavel `CENTRAL_ENABLED` ausente do ambiente: sua presenca seleciona a fonte
por ambiente e impede editar as credenciais pela tela, mesmo com valor false.

Preencher origem HTTPS do Central, token exclusivo COMERCIAL e HMAC correspondente.
Nao ativar ate conferir clientes, assinaturas, bonificacoes e vinculos. Nao
reutilizar credenciais PROPOSTAS. Manter purga desabilitada.

## Retorno

O ponto anterior a esta publicacao e a tag `restauracao-comercial-20261116-183142`,
commit `4f341b50f92cbf395d9af1326427cf7fc91179b6`.

Para retornar o codigo, selecionar a revisao anterior no Render. Nao usar
`git reset --hard`, nao apagar dados e nao executar automaticamente o dump MySQL.
As tabelas aditivas podem permanecer durante o rollback de codigo. Restauracao de
dados requer decisao separada para nao perder gravacoes posteriores ao backup.

O backup local privado possui bundle verificado e copia dos fontes anteriores.
Ele nao deve ser enviado ao Git: o bundle preserva historico com arquivo de ambiente
antigo. Remover esse arquivo do commit atual nao o remove do historico; as
credenciais eventualmente expostas no passado exigem revisao e rotacao coordenada.
O hook Render antigo tambem estava versionado e deve ser rotacionado pelo operador.