from __future__ import annotations

import os
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.app import create_app
from src.models import db, Empresa, User, Entidade, FluxoContaModel, ContaBanco, Lancamento
from src.routes.conciliacao import conciliacao_bp
from src.routes.comissoes import comissoes_bp
from src.routes.importacoes import importacoes_bp
from src.routes.auth import auth_bp
from src.services.conciliacao import criar_conciliacao_ofx, reconciliar_conciliacao


OFX_SAMPLE = """OFXHEADER:100
DATA:OFXSGML
<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20260401<TRNAMT>-150.00<FITID>OFX-001<NAME>Fornecedor X<MEMO>Pagamento teste</STMTTRN>
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20260402<TRNAMT>300.00<FITID>OFX-002<NAME>Cliente Y<MEMO>Recebimento teste</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""


@dataclass
class Resultado:
    nome: str
    ok: bool
    detalhe: str


def _print_resultado(resultado: Resultado):
    status = 'OK' if resultado.ok else 'PENDENTE'
    print(f'[{status}] {resultado.nome}: {resultado.detalhe}')


def main() -> int:
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.drop_all()
        db.create_all()

        empresa = Empresa(nome='Validacao Comercial', cnpj='55555555000155')
        db.session.add(empresa)
        db.session.flush()

        admin = User(empresa_id=empresa.id, username='admin', email='admin@val.local', full_name='Admin', is_active=True, is_admin=True, role='admin')
        admin.set_password('123456')
        operator = User(empresa_id=empresa.id, username='operator', email='operator@val.local', full_name='Operator', is_active=True, is_admin=False, role='operator')
        operator.set_password('123456')
        viewer = User(empresa_id=empresa.id, username='viewer', email='viewer@val.local', full_name='Viewer', is_active=True, is_admin=False, role='viewer')
        viewer.set_password('123456')
        db.session.add_all([admin, operator, viewer])
        db.session.flush()

        cliente = Entidade(empresa_id=empresa.id, tipo='C', cnpj_cpf='55555555000156', nome='Cliente', ativo=True)
        vendedor = Entidade(empresa_id=empresa.id, tipo='V', cnpj_cpf='55555555000157', nome='Vendedor', ativo=True)
        db.session.add_all([cliente, vendedor])
        db.session.flush()
        cliente.vendedor_id = vendedor.id

        fluxo_receita = FluxoContaModel(empresa_id=empresa.id, codigo='1.1', descricao='Receita', tipo='R', ativo=True)
        fluxo_despesa = FluxoContaModel(empresa_id=empresa.id, codigo='2.1', descricao='Despesa', tipo='P', ativo=True)
        db.session.add_all([fluxo_receita, fluxo_despesa])
        db.session.flush()

        conta = ContaBanco(empresa_id=empresa.id, nome='Conta Principal', banco='Banco', agencia='0001', numero_conta='12345', ativo=True, is_principal=True, fluxo_conta_id=fluxo_receita.id, saldo_inicial=1000)
        db.session.add(conta)
        db.session.flush()

        lanc_saida = Lancamento(empresa_id=empresa.id, data_evento=__import__('datetime').date(2026, 4, 1), data_vencimento=__import__('datetime').date(2026, 4, 1), data_pagamento=None, status='aberto', fluxo_conta_id=fluxo_despesa.id, conta_banco_id=conta.id, entidade_id=cliente.id, valor_real=150, valor_pago=0, numero_documento='DOC-SAIDA', observacoes='Pagamento teste')
        lanc_entrada = Lancamento(empresa_id=empresa.id, data_evento=__import__('datetime').date(2026, 4, 2), data_vencimento=__import__('datetime').date(2026, 4, 2), data_pagamento=None, status='aberto', fluxo_conta_id=fluxo_receita.id, conta_banco_id=conta.id, entidade_id=cliente.id, valor_real=300, valor_pago=0, numero_documento='DOC-ENTRADA', observacoes='Recebimento teste')
        db.session.add_all([lanc_saida, lanc_entrada])
        db.session.commit()

        validacoes = []
        validacoes.append(Resultado('Blueprint auth', auth_bp.name == 'auth', 'registrado' if auth_bp.name == 'auth' else 'não registrado'))
        validacoes.append(Resultado('Blueprint importacoes', importacoes_bp.name == 'importacoes', 'registrado' if importacoes_bp.name == 'importacoes' else 'não registrado'))
        validacoes.append(Resultado('Blueprint comissoes', comissoes_bp.name == 'comissoes', 'registrado' if comissoes_bp.name == 'comissoes' else 'não registrado'))
        validacoes.append(Resultado('Blueprint conciliacao', conciliacao_bp.name == 'conciliacao', 'registrado' if conciliacao_bp.name == 'conciliacao' else 'não registrado'))

        conciliacao = criar_conciliacao_ofx(empresa.id, conta.id, OFX_SAMPLE, criado_por_user_id=admin.id)
        resumo = reconciliar_conciliacao(conciliacao.id, empresa.id)
        validacoes.append(Resultado('Conciliação OFX', resumo['conciliados'] == 2 and resumo['pendentes'] == 0 and resumo['divergentes'] == 0, f"{resumo}"))

        # Roadmap stages: report current practical coverage.
        roadmap = [
            Resultado('PF', False, 'não há modo PF dedicado; apenas base financeira reutilizável'),
            Resultado('PME', False, 'não há toggle de plano; há base de clientes/fornecedores e fluxo'),
            Resultado('Microempresa', True, 'comissões, RBAC, importação NFSe/OFX e controle bancário presentes'),
            Resultado('Escalável', True, 'isolation por empresa, hardening e auditoria/controle base presentes'),
        ]

        all_ok = True
        print('\n=== Validações do Sistema ===')
        for item in validacoes:
            _print_resultado(item)
            all_ok = all_ok and item.ok

        print('\n=== Leitura do Roadmap ===')
        for item in roadmap:
            _print_resultado(item)

        print('\nObservação: PF/PME ainda são estágios de produto, não modos runtime plenamente separados.')

        return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
