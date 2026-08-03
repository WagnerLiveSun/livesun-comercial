#!/usr/bin/env python
"""
Script de inicialização do banco de dados - LiveSun Comercial
Executa as migrações e insere dados iniciais

Uso:
  python setup_db.py                          # Usar variáveis de ambiente
  python setup_db.py --init-only              # Apenas criar tabelas
  python setup_db.py --hostinger              # Para Hostinger
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app
from src.models import db, Empresa, User, Entidade, ParametroSistema
from werkzeug.security import generate_password_hash


def print_header(msg):
    print(f"\n{'=' * 70}")
    print(f"  {msg}")
    print(f"{'=' * 70}\n")


def print_success(msg):
    print(f"✓ {msg}")


def print_warning(msg):
    print(f"⚠ {msg}")


def print_error(msg):
    print(f"✗ {msg}")


def setup_database(app, init_only=False):
    """Configura o banco de dados"""
    
    with app.app_context():
        print_header("INICIALIZAR BANCO DE DADOS - LiveSun Comercial")
        
        try:
            # 1. Criar todas as tabelas
            print("[1/5] Criando tabelas...")
            db.create_all()
            print_success("Tabelas criadas/verificadas com sucesso")
            
            # 2. Criar empresa padrão se não existir
            print("\n[2/5] Verificando/criando empresa padrão...")
            empresa = Empresa.query.first()
            if not empresa:
                empresa = Empresa(
                    nome='LiveSun Comercial',
                    cnpj='00.000.000/0000-00'
                )
                db.session.add(empresa)
                db.session.commit()
                print_success("Empresa criada com sucesso")
            else:
                print_success(f"Empresa já existe: {empresa.nome}")
            
            # 3. Criar usuário padrão se não existir
            print("\n[3/5] Verificando/criando usuário padrão...")
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    empresa_id=empresa.id,
                    username='admin',
                    email='admin@livesun.local',
                    full_name='Administrador',
                    is_active=True,
                    is_admin=True,
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print_success("Usuário admin criado com sucesso")
                print_warning("Credenciais: admin / admin123")
                print_warning("⚠️  MUDE A SENHA IMEDIATAMENTE EM PRODUÇÃO!")
            else:
                print_success("Usuário admin já existe")
            
            # 4. Criar parâmetro padrão de comissão
            print("\n[4/5] Verificando/criando parâmetros de sistema...")
            param = ParametroSistema.query.filter_by(
                empresa_id=empresa.id,
                chave='aliquota_comissao_padrao'
            ).first()
            if not param:
                param = ParametroSistema(
                    empresa_id=empresa.id,
                    chave='aliquota_comissao_padrao',
                    valor='5.00',
                    tipo='numeric',
                    descricao='Alíquota padrão de comissão sobre vendas'
                )
                db.session.add(param)
                db.session.commit()
                print_success("Parâmetro aliquota_comissao_padrao criado")
            else:
                print_success("Parâmetro aliquota_comissao_padrao já existe")
            
            # 5. Criar entidades de exemplo (opcional)
            if not init_only:
                print("\n[5/5] Criando entidades de exemplo...")
                
                # Criar vendedor padrão
                vendedor = Entidade.query.filter_by(
                    empresa_id=empresa.id,
                    tipo='V',
                    nome='Vendedor Padrão'
                ).first()
                
                if not vendedor:
                    vendedor = Entidade(
                        empresa_id=empresa.id,
                        tipo='V',
                        cnpj_cpf='00000000000191',
                        nome='Vendedor Padrão',
                        email='vendedor@livesun.local',
                        ativo=True
                    )
                    db.session.add(vendedor)
                    db.session.commit()
                    print_success("Vendedor padrão criado")
                else:
                    print_success("Vendedor padrão já existe")
                
                # Criar cliente padrão
                cliente = Entidade.query.filter_by(
                    empresa_id=empresa.id,
                    tipo='C',
                    nome='Cliente Padrão'
                ).first()
                
                if not cliente:
                    cliente = Entidade(
                        empresa_id=empresa.id,
                        tipo='C',
                        cnpj_cpf='00000000000191',
                        nome='Cliente Padrão',
                        email='cliente@example.com',
                        aliquota_comissao_especifica=None,
                        valor_repasse=0.00,
                        vendedor_id=vendedor.id,
                        ativo=True
                    )
                    db.session.add(cliente)
                    db.session.commit()
                    print_success("Cliente padrão criado com vendedor vinculado")
                else:
                    print_success("Cliente padrão já existe")
            else:
                print("\n[5/5] Pulando criação de entidades (modo --init-only)")
            
            # Resumo final
            print_header("BANCO DE DADOS PRONTO!")
            print("✓ Tabelas criadas/verificadas")
            print(f"✓ Empresa: {empresa.nome}")
            print(f"✓ Usuário admin criado (senha padrão: admin123)")
            print(f"✓ Parâmetro de comissão padrão: 5.00%")
            if not init_only:
                print(f"✓ Entidades de exemplo criadas")
            
            print("\n" + "=" * 70)
            print("  PRÓXIMOS PASSOS:")
            print("=" * 70)
            print("1. Configure o arquivo .env com credenciais corretas")
            print("2. Para Hostinger:")
            print("   - Abra phpMyAdmin")
            print("   - Selecione seu banco de dados")
            print("   - Execute o SQL em: initialize_db_hostinger.sql")
            print("3. Inicie a aplicação:")
            print("   - Desenvolvimento: python run.py")
            print("   - Produção: gunicorn -w 4 'src.app:create_app()'")
            print("4. Acesse http://localhost:5000")
            print("5. Faça login com admin/admin123")
            print("6. MUDE A SENHA IMEDIATAMENTE!")
            print("\n")
            
            return True
            
        except Exception as e:
            print_header("ERRO NA INICIALIZAÇÃO")
            print_error(f"Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Inicializa o banco de dados do LiveSun Comercial'
    )
    parser.add_argument(
        '--init-only',
        action='store_true',
        help='Apenas criar tabelas, sem dados de exemplo'
    )
    parser.add_argument(
        '--hostinger',
        action='store_true',
        help='Modo Hostinger (mostra instruções)'
    )
    
    args = parser.parse_args()
    
    # Criar aplicação
    app = create_app()
    
    # Executar setup
    success = setup_database(app, init_only=args.init_only)
    
    if args.hostinger:
        print_header("INSTRUÇÕES PARA HOSTINGER")
        print("""
1. Acesse cPanel → Databases → MySQL Databases
2. Crie um novo banco de dados: u951548013_Gfinanceiro
3. Crie um novo usuário MySQL (ex: gfinanceiro)
4. Atribua TODOS OS PRIVILÉGIOS ao usuário para este banco
5. Abra phpMyAdmin
6. Selecione o banco u951548013_Gfinanceiro
7. Clique em "SQL" (ou "Import")
8. Cole o conteúdo de: initialize_db_hostinger.sql
9. Execute
10. Verifique se todas as tabelas foram criadas

Depois, configure o arquivo .env com:
  DB_HOST=srv1124.hstgr.io
  DB_USER=u951548013_gfinanceiro
  DB_PASSWORD=sua_senha_aqui
  DB_NAME=u951548013_Gfinanceiro
        """)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
