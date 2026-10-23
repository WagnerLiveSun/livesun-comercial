from pathlib import Path
import re
import shutil
from datetime import datetime

ARQUIVO = Path(r"D:\App_LiveSun\LiveSun_Comercial_X\src\templates\admin\comercial_panel.html")

conteudo = ARQUIVO.read_text(encoding="utf-8")

backup = ARQUIVO.with_name(
    f"comercial_panel_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
)
shutil.copy2(ARQUIVO, backup)

novo_set = """{% set grupos_modulos = [
    {
        'nome': 'Painéis por módulo',
        'classe': 'modulos-grupo-paineis',
        'itens': [
            {'codigo': 'dashboard_comercial', 'nome': 'Painel Comercial', 'descricao': 'Indicadores comerciais, orçamentos e pedidos'},
            {'codigo': 'dashboard_financeiro', 'nome': 'Painel Financeiro', 'descricao': 'Indicadores financeiros, saldos e fluxo de caixa'},
            {'codigo': 'dashboard_locacao', 'nome': 'Painel de Locação', 'descricao': 'Peças, contratos, retiradas e devoluções'},
            {'codigo': 'dashboard_propostas', 'nome': 'Painel de Propostas', 'descricao': 'Indicadores de propostas e conversões'},
            {'codigo': 'dashboard_fiscal', 'nome': 'Painel Fiscal', 'descricao': 'Indicadores de NFS-e emitidas e importadas'}
        ]
    },
    {
        'nome': 'Cadastros',
        'classe': '',
        'itens': [
            {'codigo': 'entidades', 'nome': 'Entidades', 'descricao': 'Clientes, fornecedores e cadastros'}
        ]
    },
    {
        'nome': 'Mercadoria',
        'classe': '',
        'itens': [
            {'codigo': 'comercial', 'nome': 'Comercial', 'descricao': 'PDV, NF-e, NFC-e e Pedidos'},
            {'codigo': 'estoque', 'nome': 'Estoque', 'descricao': 'Movimento de estoque'},
            {'codigo': 'compras', 'nome': 'Compras', 'descricao': 'Entrada de NF de compra'},
            {'codigo': 'pedidos', 'nome': 'Pedidos', 'descricao': 'Pedidos de venda'},
            {'codigo': 'pdv', 'nome': 'PDV', 'descricao': 'PDV Caixa'}
        ]
    },
    {
        'nome': 'Propostas',
        'classe': '',
        'itens': [
            {'codigo': 'propostas', 'nome': 'Propostas Comerciais', 'descricao': 'Gestão de propostas comerciais'},
            {'codigo': 'aprovacao', 'nome': 'Aprovação de Propostas', 'descricao': 'Aprovação de propostas'}
        ]
    },
    {
        'nome': 'Serviços / Fiscal',
        'classe': '',
        'itens': [
            {'codigo': 'servicos', 'nome': 'Serviços / Fiscal', 'descricao': 'NFS-e e Importação de Notas'}
        ]
    },
    {
        'nome': 'Locação',
        'classe': '',
        'itens': [
            {'codigo': 'locacao', 'nome': 'Locação', 'descricao': 'Aluguel de Roupas e Fantasias'}
        ]
    },
    {
        'nome': 'Contratos',
        'classe': '',
        'itens': [
            {'codigo': 'contratos', 'nome': 'Contratos', 'descricao': 'Gestão de Contratos de Serviços'}
        ]
    },
    {
        'nome': 'Financeiro',
        'classe': '',
        'itens': [
            {'codigo': 'financeiro', 'nome': 'Financeiro', 'descricao': 'Gestão Financeira e Fluxo de Caixa'},
            {'codigo': 'fluxo', 'nome': 'Fluxo Caixa', 'descricao': 'Movimentação de caixa'},
            {'codigo': 'contas_banco', 'nome': 'Contas Banco', 'descricao': 'Contas bancárias'}
        ]
    },
    {
        'nome': 'Relatórios',
        'classe': '',
        'itens': [
            {'codigo': 'relatorios', 'nome': 'Relatórios', 'descricao': 'Relatórios gerenciais e fiscais'}
        ]
    },
    {
        'nome': 'Admin',
        'classe': '',
        'itens': [
            {'codigo': 'usuarios', 'nome': 'Usuários', 'descricao': 'Gerenciar Usuários'},
            {'codigo': 'controle_acesso', 'nome': 'Controle de Acesso', 'descricao': 'Controle de Acesso'}
        ]
    }
] %}"""

novo_loop = """{% for grupo in grupos_modulos %}
<section
    class="ls-card modulos-grupo{% if grupo.classe %} {{ grupo.classe }}{% endif %}"
    aria-label="{{ grupo.nome }}">

    <table class="table ls-theme-table modulos-grupo-table">
        <thead>
            <tr>
                <th scope="col">
                    {{ grupo.nome }}
                </th>
            </tr>
        </thead>
    </table>

    <div class="modulos-grupo-itens">
        {% for item in grupo.itens %}
        <label
            class="modulo-item{% if modulo_disabled %} modulo-item-bloqueado{% endif %}"
            for="mod_{{ r.empresa_id }}_{{ item.codigo }}">

            <span class="form-switch modulo-controle">
                <input
                    class="form-check-input"
                    type="checkbox"
                    name="modulo_{{ item.codigo }}"
                    id="mod_{{ r.empresa_id }}_{{ item.codigo }}"
                    {% if mod.get(item.codigo) %}checked{% endif %}
                    {% if modulo_disabled %}disabled{% endif %}>
            </span>

            <span class="modulo-texto">
                <span class="modulo-nome">
                    {{ item.nome }}
                </span>

                <span class="modulo-descricao text-muted">
                    {{ item.descricao }}
                </span>
            </span>
        </label>
        {% endfor %}
    </div>
</section>
{% endfor %}"""

# 1. Substitui o set grupos_modulos antigo, do {% set ... = [ até o primeiro ] %}
padrao_set = re.compile(
    r"\{%\s*set\s+grupos_modulos\s*=\s*\[.*?\]\s*%\}",
    re.DOTALL
)

conteudo, qtd_set = padrao_set.subn(novo_set, conteudo, count=1)

# 2. Substitui o loop antigo:
# {% for grupo_nome, grupo_itens in grupos_modulos %}
#   ... {% for codigo, nome, descricao in grupo_itens %} ... {% endfor %}
# ... {% endfor %}
padrao_loop = re.compile(
    r"\{%\s*for\s+grupo_nome\s*,\s*grupo_itens\s+in\s+grupos_modulos\s*%\}.*?"
    r"\{%\s*endfor\s*%\}.*?\{%\s*endfor\s*%\}",
    re.DOTALL
)

conteudo, qtd_loop = padrao_loop.subn(novo_loop, conteudo, count=1)

if qtd_set != 1 or qtd_loop != 1:
    raise RuntimeError(
        f"Substituição incompleta. set={qtd_set}, loop={qtd_loop}. "
        "Nada foi salvo; verifique se o arquivo ainda contém o código antigo."
    )

ARQUIVO.write_text(conteudo, encoding="utf-8")

print("Backup criado em: - corrigir_comercial_panel.py:174", backup)
print("Bloco grupos_modulos substituído. - corrigir_comercial_panel.py:175")
print("Loop de módulos substituído. - corrigir_comercial_panel.py:176")
print("Arquivo corrigido: - corrigir_comercial_panel.py:177", ARQUIVO)