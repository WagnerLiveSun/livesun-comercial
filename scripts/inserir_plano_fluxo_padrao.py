# Script para inserir plano de fluxo de caixa padrão para todas as empresas
# Executar manualmente após deploy ou incluir na inicialização

from src.app import create_app
from src.models import db, Empresa, FluxoContaModel
from sqlalchemy.exc import IntegrityError

# Estrutura do plano de contas padrão (baseado no CSV fornecido)
PLANO_PADRAO = [
    # (codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico)
    ("1", "Entradas de Caixa", "R", None, 1, None),
    ("1.1", "Receitas Operacionais", "R", None, 2, None),
    ("1.1.1", "Vendas à vista", "R", None, 3, 1),
    ("1.1.2", "Vendas cartão crédito", "R", None, 3, 1),
    ("1.1.3", "Vendas cartão débito", "R", None, 3, 1),
    ("1.1.4", "Recebimento mensalidades/serviços", "R", None, 3, 1),
    ("1.2", "Receitas Financeiras", "R", None, 2, None),
    ("1.2.1", "Juros recebidos", "R", None, 3, 1),
    ("1.2.2", "Descontos obtidos", "R", None, 3, 1),
    ("1.3", "Outras Entradas", "R", None, 2, None),
    ("1.3.1", "Empréstimos recebidos", "R", None, 3, 1),
    ("1.3.2", "Aporte de sócios", "R", None, 3, 1),
    ("1.3.3", "Reembolsos diversos", "R", None, 3, 1),
    ("2", "Saídas de Caixa", "P", None, 1, None),
    ("2.1", "Custos Operacionais", "P", None, 2, None),
    ("2.1.1", "Compra de mercadorias", "P", None, 3, 1),
    ("2.1.2", "Matéria-prima/insumos", "P", None, 3, 1),
    ("2.1.3", "Fretes sobre compras", "P", None, 3, 1),
    ("2.2", "Despesas Fixas", "P", None, 2, None),
    ("2.2.1", "Aluguel", "P", None, 3, 1),
    ("2.2.2", "Energia elétrica", "P", None, 3, 1),
    ("2.2.3", "Água", "P", None, 3, 1),
    ("2.2.4", "Internet e telefone", "P", None, 3, 1),
    ("2.3", "Despesas com Pessoal", "P", None, 2, None),
    ("2.3.1", "Salários", "P", None, 3, 1),
    ("2.3.2", "Encargos (INSS, FGTS)", "P", None, 3, 1),
    ("2.3.3", "Pró-labore", "P", None, 3, 1),
    ("2.4", "Despesas Variáveis", "P", None, 2, None),
    ("2.4.1", "Comissões sobre vendas", "P", None, 3, 1),
    ("2.4.2", "Taxas de cartão/maquininha", "P", None, 3, 1),
    ("2.4.3", "Impostos sobre vendas", "P", None, 3, 1),
    ("2.5", "Despesas Financeiras", "P", None, 2, None),
    ("2.5.1", "Juros e multas pagas", "P", None, 3, 1),
    ("2.5.2", "Tarifas bancárias", "P", None, 3, 1),
    ("2.6", "Outras Saídas", "P", None, 2, None),
    ("2.6.1", "Distribuição de lucros", "P", None, 3, 1),
    ("2.6.2", "Adiantamentos a sócios", "P", None, 3, 1),
]

def inserir_plano_padrao_para_todas_empresas():
    app = create_app()
    with app.app_context():
        empresas = Empresa.query.all()
        for empresa in empresas:
            for codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico in PLANO_PADRAO:
                # Evita duplicidade
                existe = FluxoContaModel.query.filter_by(empresa_id=empresa.id, codigo=codigo).first()
                if not existe:
                    conta = FluxoContaModel(
                        empresa_id=empresa.id,
                        codigo=codigo,
                        descricao=descricao,
                        tipo=tipo,
                        mascara=mascara,
                        nivel_sintetico=nivel_sintetico,
                        nivel_analitico=nivel_analitico,
                        ativo=True
                    )
                    db.session.add(conta)
            try:
                db.session.commit()
                print(f"Plano padrão inserido para empresa {empresa.nome} (ID={empresa.id})")
            except IntegrityError:
                db.session.rollback()
                print(f"Erro de integridade ao inserir para empresa {empresa.nome} (ID={empresa.id})")

if __name__ == "__main__":
    inserir_plano_padrao_para_todas_empresas()
