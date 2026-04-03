"""
Script de migração para adicionar suporte a comissões
Este script adiciona as novas tabelas e campos necessários para o módulo de comissões
"""

import os
import sys
from datetime import datetime

# Adicionar o caminho do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app
from src.models import db, Lancamento, Entidade, Comissao, ParametroSistema

def run_migrations():
    """Executa as migrações necessárias"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("[MIGRAÇÃO] Iniciando processo de migração para COMISSÕES")
        print("=" * 60)
        print()
        
        try:
            # 1. Criar tabelas do zero se não existirem
            print("[1/3] Criando tabelas...")
            db.create_all()
            print("✓ Tabelas criadas/verificadas com sucesso")
            print()
            
            # 2. Adicionar campos às tabelas existentes (se necessário)
            # A SQLAlchemy não consegue adicionar campos automaticamente,
            # então isso deve ser feito via SQL direto ou Alembic
            print("[2/3] Verificando campos em tabelas existentes...")
            
            # Verificar se as colunas existem
            conn = db.engine.raw_connection()
            cursor = conn.cursor()
            
            # Verificar coluna valor_imposto em lancamentos
            try:
                cursor.execute("SELECT valor_imposto FROM lancamentos LIMIT 1")
                print("✓ Campo 'valor_imposto' em lancamentos já existe")
            except Exception as e:
                print("⚠ Campo 'valor_imposto' pode precisar ser criado:")
                print("  ALTER TABLE lancamentos ADD COLUMN valor_imposto DECIMAL(15,2) DEFAULT 0.00;")
            
            # Verificar coluna valor_outros_custos em lancamentos
            try:
                cursor.execute("SELECT valor_outros_custos FROM lancamentos LIMIT 1")
                print("✓ Campo 'valor_outros_custos' em lancamentos já existe")
            except Exception as e:
                print("⚠ Campo 'valor_outros_custos' pode precisar ser criado:")
                print("  ALTER TABLE lancamentos ADD COLUMN valor_outros_custos DECIMAL(15,2) DEFAULT 0.00;")
            
            # Verificar campos em entidades
            try:
                cursor.execute("SELECT aliquota_comissao_especifica FROM entidades LIMIT 1")
                print("✓ Campo 'aliquota_comissao_especifica' em entidades já existe")
            except Exception as e:
                print("⚠ Campo 'aliquota_comissao_especifica' pode precisar ser criado:")
                print("  ALTER TABLE entidades ADD COLUMN aliquota_comissao_especifica DECIMAL(5,2);")
            
            try:
                cursor.execute("SELECT valor_repasse FROM entidades LIMIT 1")
                print("✓ Campo 'valor_repasse' em entidades já existe")
            except Exception as e:
                print("⚠ Campo 'valor_repasse' pode precisar ser criado:")
                print("  ALTER TABLE entidades ADD COLUMN valor_repasse DECIMAL(10,2) DEFAULT 0.00;")
            
            try:
                cursor.execute("SELECT vendedor_id FROM entidades LIMIT 1")
                print("✓ Campo 'vendedor_id' em entidades já existe")
            except Exception as e:
                print("⚠ Campo 'vendedor_id' pode precisar ser criado:")
                print("  ALTER TABLE entidades ADD COLUMN vendedor_id INT;")
                print("  ALTER TABLE entidades ADD FOREIGN KEY (vendedor_id) REFERENCES entidades(id);")
            
            cursor.close()
            conn.close()
            
            print()
            
            # 3. Criar parâmetro padrão se não existir
            print("[3/3] Inicializando parâmetros de sistema...")
            
            from src.models import Empresa
            empresas = Empresa.query.all()
            
            for empresa in empresas:
                param = ParametroSistema.query.filter_by(
                    empresa_id=empresa.id,
                    chave='aliquota_comissao_padrao'
                ).first()
                
                if not param:
                    param = ParametroSistema(
                        empresa_id=empresa.id,
                        chave='aliquota_comissao_padrao',
                        valor='5.00',  # Alíquota padrão de 5%
                        tipo='numeric',
                        descricao='Alíquota padrão de comissão sobre vendas'
                    )
                    db.session.add(param)
                    print(f"✓ Parâmetro criado para empresa: {empresa.nome}")
                else:
                    print(f"✓ Parâmetro já existe para empresa: {empresa.nome}")
            
            db.session.commit()
            
            print()
            print("=" * 60)
            print("[SUCESSO] Migração concluída com sucesso!")
            print("=" * 60)
            print()
            print("Próximos passos:")
            print("1. Verifique se há campos pendentes acima e execute os comandos SQL")
            print("2. Configure a alíquota padrão em: /comissoes/parametros")
            print("3. Configure vendedores em: /entidades (tipo: Vendedor)")
            print("4. Configure clientes com alíquota e vendedor em: /entidades (tipo: Cliente)")
            print()
            
        except Exception as e:
            print()
            print("=" * 60)
            print("[ERRO] Erro durante a migração!")
            print("=" * 60)
            print(f"Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
