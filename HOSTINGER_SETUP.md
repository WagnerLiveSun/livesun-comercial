# Hostinger - Instalação do LiveSun Comercial

## 1. Criar o banco
No hPanel da Hostinger, crie um banco MySQL novo e um usuário MySQL novo.

## 2. Executar o schema
Abra o phpMyAdmin do banco criado e execute o arquivo [install_hostinger_comercial.sql](install_hostinger_comercial.sql).

Antes de executar, ajuste esta linha no script:
```sql
USE SEU_BANCO_HOSTINGER;
```
Substitua por algo como:
```sql
USE u123456789_comercial;
```

## 3. Configurar a aplicação
No painel da aplicação, configure as variáveis:
```env
DB_TYPE=mysql
DB_HOST=seu-host-mysql-da-hostinger
DB_PORT=3306
DB_USER=seu-usuario-mysql
DB_PASSWORD=sua-senha-mysql
DB_NAME=nome_real_do_banco
```

## 4. Subir a aplicação
- A aplicação deve ser publicada com o código do LiveSun Comercial.
- O `DB_NAME` do ambiente deve ser igual ao banco usado no `USE` do script.
- Se o deploy usar Gunicorn, o entrypoint continua sendo `src.app:create_app()`.

## 5. Pós-instalação
- Verifique se o login abre com a empresa inicial criada pelo script.
- Ajuste a senha do admin padrão após o primeiro acesso.
- Se quiser importar dados antigos, faça isso depois de validar o login e as tabelas.
