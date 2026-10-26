"""Disponibilidade comercial por módulo e autorização funcional por usuário.

Os nomes de endpoints abaixo correspondem às rotas existentes. Campos legados
de funções (fluxo, contas_banco, estoque etc.) não são seletores comerciais.
"""

from dataclasses import dataclass

from src.services.planos import plan_allows_endpoint, plan_rank


MODULE_LABELS = {
    'entidades': {'label': 'Cadastros', 'descricao': 'Entidades, filiais, produtos, serviços e tabelas de preço'},
    'comercial': {'label': 'Comercial', 'descricao': 'Estoque, compras, pedidos e PDV'},
    'propostas': {'label': 'Propostas', 'descricao': 'Propostas comerciais e aprovação'},
    'servicos': {'label': 'Serviços / Fiscal', 'descricao': 'NFS-e e rotinas fiscais'},
    'locacao': {'label': 'Locação', 'descricao': 'Acervo, agenda, orçamentos e contratos de locação'},
    'contratos': {'label': 'Contratos', 'descricao': 'Contratos de vendas e cláusulas padrão'},
    'financeiro': {'label': 'Financeiro', 'descricao': 'Contas, lançamentos, OFX, conciliação e comissões'},
    # Reutiliza a coluna existente; não exige migração de banco.
    'usuarios': {'label': 'Administração', 'descricao': 'Usuários, controle de acesso e relatório de usuários'},
}


@dataclass(frozen=True)
class AccessRule:
    module: str | None
    permission: str
    level: int = 1


ENDPOINT_ACCESS_RULES = {}


def _register(blueprint, names, module, permission, level=1):
    for name in names.split():
        ENDPOINT_ACCESS_RULES[f'{blueprint}.{name}'] = AccessRule(module, permission, level)


_register('dashboard', 'index', None, 'dashboard')
for name, module, level in (
    ('comercial', 'comercial', 2), ('financeiro', 'financeiro', 1),
    ('fiscal', 'servicos', 2), ('locacao', 'locacao', 2), ('propostas', 'propostas', 1),
):
    _register('dashboard', name, module, 'dashboard', level)

_register('entidades', 'index criar editar ver deletar api_search', 'entidades', 'entidades')
_register('fluxo', 'index criar editar deletar api_search', 'financeiro', 'fluxo', 2)
_register('contas_banco', 'index criar editar ver deletar api_search', 'financeiro', 'contas_banco')
_register('lancamentos', 'index criar editar pagar deletar', 'financeiro', 'lancamentos')
_register('comissoes', 'listar relatorio apurar parametros exportar_csv', 'financeiro', 'comissoes', 2)
_register('conciliacao', 'index nova detalhe reconciliar vincular_item desvincular_item', 'financeiro', 'conciliacao', 2)
_register('importacoes', 'importar_nfse', 'servicos', 'importar_nfse', 2)
_register('importacoes', 'importar_ofx', 'financeiro', 'importar_ofx', 2)
_register('auth', 'add_user add_user_config', 'usuarios', 'usuarios', 2)
_register('auth', 'controle_acesso controle_processos controle_usuario_permissoes', 'usuarios', 'controle_acesso', 2)

for names, module, permission, level in (
    ('filiais_index filiais_criar filiais_editar filiais_deletar', 'entidades', 'comercial_filiais', 1),
    ('produtos_index produtos_criar produtos_editar produtos_deletar', 'entidades', 'comercial_produtos', 1),
    ('servicos_index servicos_criar servicos_editar servicos_deletar', 'entidades', 'comercial_servicos', 1),
    ('tabelas_preco_index tabelas_preco_criar tabelas_preco_editar tabelas_preco_itens tabelas_preco_itens_adicionar tabelas_preco_itens_remover', 'entidades', 'comercial_tabelas_preco', 2),
    ('estoque_index estoque_criar', 'comercial', 'comercial_estoque', 2),
    ('compras_index compras_importar_xml compras_xml_validar compras_xml_confirmar compras_xml_cancelar compras_criar compras_detalhe compras_editar compras_excluir', 'comercial', 'comercial_compras', 2),
    ('documentos_index documentos_criar documentos_detalhe', 'servicos', 'comercial_documentos', 2),
    ('orcamentos_index orcamentos_criar orcamentos_editar orcamentos_detalhe orcamentos_exportar_pdf orcamentos_exportar_pdf_resumido orcamentos_converter', 'propostas', 'comercial_orcamentos', 1),
    ('propostas_aprovacao orcamentos_aprovar orcamentos_reprovar', 'propostas', 'comercial_orcamentos', 1),
    ('pedidos_index pedidos_detalhe pedidos_faturar_previa pedidos_faturar', 'comercial', 'comercial_pedidos', 2),
    ('pdv_index pdv_abrir pdv_vender pdv_venda_adicionar_item pdv_venda_finalizar pdv_venda_imprimir pdv_fechar', 'comercial', 'comercial_pdv', 2),
):
    _register('comercial_operacional', names, module, permission, level)

_register('nfse_nacional', '''index configuracoes tomadores servicos emissoes emissao_detalhe
    emissao_download_dps emissao_download_nfse emissao_imprimir_danfs cancelamento
    cancelar_emissao nfse_consultar listagem replicar_emissao visualizar enviar_email
    nfse_cancelamento_substituicao nfse_consultar_imprimir''', 'servicos', 'nfse_nacional', 2)

for names, permission in (
    ('clausulas_lista', 'clausulas_view'), ('clausulas_criar', 'clausulas_create'),
    ('clausulas_editar', 'clausulas_edit'), ('index visualizar historico baixar_anexo', 'contratos_view'),
    ('gerar_orcamento', 'contratos_create'), ('editar reordenar_clausulas', 'contratos_edit'),
    ('assinar', 'contratos_sign'), ('cancelar', 'contratos_delete'),
    ('exportar_pdf exportar_docx', 'contratos_export'),
):
    _register('contratos', names, 'contratos', permission)

for names, permission in (
    ('acervo_lista acervo_criar acervo_editar acervo_disponibilidade api_pecas api_kits', 'locacao_acervo'),
    ('orcamentos_lista orcamentos_criar orcamentos_editar orcamentos_converter_reserva contratos_lista contratos_visualizar relatorio_receita api_clientes', 'locacao_contratos'),
    ('operacao_agenda relatorio_disponibilidade api_disponibilidade_peca', 'locacao_agenda'),
    ('operacao_retirada operacao_devolucao operacao_inspecao', 'locacao_operacao'),
):
    _register('locacao', names, 'locacao', permission, 2)

for names, module, level in (
    ('usuarios', 'usuarios', 1), ('entidades', 'entidades', 1),
    ('clientes_comissao', 'entidades', 2), ('orcamentos', 'propostas', 1),
    ('pedidos estoque compras', 'comercial', 2), ('saldo_contas', 'financeiro', 1),
    ('fluxo_categorias', 'financeiro', 2), ('nfse', 'servicos', 2),
    ('locacao_pecas locacao_contratos locacao_manutencao', 'locacao', 2),
    ('contratos', 'contratos', 1),
):
    _register('relatorios_p1', names, module, 'relatorios', level)
_register('relatorios', 'listagem_notas_nfse export_listagem_notas_nfse', 'servicos', 'relatorios', 2)
_register('relatorios', '''listagem_lancamentos export_listagem_lancamentos fluxo_caixa_csv
    export_fluxo_caixa_csv fluxo_caixa_previsto fluxo_caixa_realizado fluxo_caixa
    export_fluxo_caixa_xlsx export_fluxo_caixa''', 'financeiro', 'relatorios', 2)
_register('relatorio_fluxo', 'index exportar', 'financeiro', 'relatorios', 2)

MANAGED_BLUEPRINTS = {endpoint.split('.')[0] for endpoint in ENDPOINT_ACCESS_RULES} - {'auth'}


def endpoint_is_managed(endpoint):
    return endpoint in ENDPOINT_ACCESS_RULES or endpoint.split('.')[0] in MANAGED_BLUEPRINTS


def endpoint_plan_allows(plan, endpoint):
    rule = ENDPOINT_ACCESS_RULES.get(endpoint)
    if rule is not None:
        return plan_rank(plan) >= rule.level
    return plan_allows_endpoint(plan, endpoint)


def can_access_endpoint(user, endpoint):
    from src.access_control import has_permission_key

    rule = ENDPOINT_ACCESS_RULES.get(endpoint)
    if rule is None or not getattr(user, 'is_authenticated', False):
        return False
    empresa = getattr(user, 'empresa', None)
    if rule.module and (
        empresa is None or not getattr(user, 'empresa_id', None)
        or not getattr(empresa, f'atividade_{rule.module}', False)
    ):
        return False
    return (
        endpoint_plan_allows(getattr(empresa, 'plano', 'premium'), endpoint)
        and has_permission_key(user, rule.permission)
    )


def update_company_modules(empresa, form):
    """Altera somente módulos; preserva permissões e campos legados de funções."""
    for key in MODULE_LABELS:
        setattr(empresa, f'atividade_{key}', f'modulo_{key}' in form)