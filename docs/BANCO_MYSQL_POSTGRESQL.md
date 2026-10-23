# Banco MySQL e PostgreSQL/MontuDB

A aplicacao escolhe o banco por configuracao de ambiente. Rotas, templates e regras de negocio nao devem testar o engine.

## Variavel de selecao

- `DB_ENGINE=mysql` (padrao)
- `DB_ENGINE=postgresql` ou `DB_ENGINE=postgres`

Alias legado: `DB_TYPE` (mesmo significado). Se os dois existirem, `DB_ENGINE` prevalece.

Variaveis `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_NAME` continuam validas (Hostinger/Render).

## MySQL (Hostinger, operacao atual)

Role: usuario MySQL da aplicacao (nao e role PostgreSQL).

```env
DB_ENGINE=mysql
MYSQL_HOST=seu-host-mysql-hostinger
MYSQL_PORT=3306
MYSQL_DATABASE=nome_do_banco_mysql
MYSQL_USER=usuario_mysql
MYSQL_PASSWORD=senha_mysql
```

Ou o formato legado:

```env
DB_TYPE=mysql
DB_HOST=seu-host-mysql-hostinger
DB_PORT=3306
DB_NAME=nome_do_banco_mysql
DB_USER=usuario_mysql
DB_PASSWORD=senha_mysql
```

Nenhum SQL de PostgreSQL (`set_config`, schema `security`) e executado neste modo.

Filtros `empresa_id` no codigo permanecem.

## PostgreSQL / MontuDB (tunel SSH local)

O tunel SSH e externo a aplicacao. Host da URI: `127.0.0.1`, porta `55432`.

Role de runtime: **livesun_api** (nunca `postgres`, `comercial_db_owner` ou `livesun_etl`).

Database: **comercial**. Schema operacional: **app**. Schema de seguranca: **security**. Search path: `app, security, pg_catalog`.

```env
DB_ENGINE=postgresql
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=55432
POSTGRES_DATABASE=comercial
POSTGRES_USER=livesun_api
POSTGRES_PASSWORD=defina_em_arquivo_local_nao_versionado
POSTGRES_RLS_ENABLED=true
```

Antes das queries tenant, a aplicacao executa `SELECT set_config('app.empresa_id', :empresa_id, true)` na transacao atual (`SET LOCAL`). O valor vem do usuario autenticado (`current_user.empresa_id` / sessao Flask-Login), nunca de query string, form, header ou JSON livre.

Filtros explicitos por `empresa_id` no codigo sao mantidos. O RLS e barreira adicional.

Admin LiveSun sem `empresa_id` nao recebe `set_config` de tenant.

Login, registro, recuperacao de senha, static, `/suporte` e webhooks publicos nao aplicam RLS (usuario ainda nao autenticado). Policies do PostgreSQL precisam permitir o SELECT de login na tabela `users` sem contexto de tenant.

## Como rodar

MySQL: configure `DB_ENGINE=mysql` (ou `DB_TYPE=mysql`) e suba `python run.py`.

PostgreSQL: abra o tunel SSH para `127.0.0.1:55432`, configure `DB_ENGINE=postgresql` com `livesun_api`, depois `python run.py`.

Credenciais reais ficam so no `.env` local, fora do Git. Use `.env.example` como modelo.

## Transacoes

O padrao existente de `commit`/`rollback` nos services e rotas foi preservado. Nao ha commit automatico no teardown.

Ha commits internos em login/cadastro, bootstrap, NFS-e, conciliacao, comercial, contratos e correlatos. Apos commit ou rollback, uma nova transacao reaplica o RLS no PostgreSQL (`after_begin`).

## Testes

```bash
python -m unittest tests.test_database_config tests.test_tenant_context tests.test_tenant_isolation -v
```

Teste de integracao PostgreSQL (opcional, requer tunel e senha local):

```bash
set LIVESUN_POSTGRES_ITEST=true
python -m unittest tests.test_postgres_runtime -v
```
