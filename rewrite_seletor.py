path = 'src/templates/admin/comercial_panel.html'
with open(path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

inicio_seletor = None
fim_seletor = None
for i, linha in enumerate(linhas):
    if 'atualizar_modulos' in linha and 'form method' in linha:
        inicio_seletor = i
    if inicio_seletor is not None and '<div class="col-12 mt-2">' in linha:
        fim_seletor = i
        break

print(f"Inicio: {inicio_seletor+1}, Fim: {fim_seletor+1}")

# Novo seletor: grade pura 4 colunas por linha, sem h6 títulos grandes
# Padrão tema: form-check form-switch com labels pequenos
# Propostas têm grupo próprio como solicitado

seletor_lines = []

# Dashboard - sempre visível, fora do grid de ativação
seletor_lines.append('            <div class="mb-3">')
seletor_lines.append('                <div class="form-check form-switch disabled">')
seletor_lines.append('                    <input class="form-check-input" type="checkbox" name="modulo_dashboard" id="mod_{{ r.empresa_id }}_dashboard" checked disabled>')
seletor_lines.append('                    <label class="form-check-label small fw-semibold text-muted" for="mod_{{ r.empresa_id }}_dashboard">Dashboard Gerencial</label>')
seletor_lines.append('                    <div class="small text-muted">Painel inicial do sistema <span class="text-success"><i class="fas fa-check-circle"></i> Sempre ativo</span></div>')
seletor_lines.append('                </div>')
seletor_lines.append('            </div>')

# Função para adicionar item de checkbox (retorna linhas de string)
def add_checkbox_line(nome_modulo, label, descricao=''):
    '''Adiciona item de checkbox no padrão do tema'''
    # Cada checkbox fica sozinho - o grid 4 por linha é gerenciado pelo CSS
    # O nome do módulo usa underscore, o label tem o texto completo
    line = '            <div class="form-check form-switch">'
    line += '<input class="form-check-input" type="checkbox" name="modulo_' + nome_modulo + '" id="mod_{{ r.empresa_id }}_' + nome_modulo + '"'
    line += ' {% if r.modulos.get(\'' + nome_modulo + '\') %}checked{% endif %}'
    line += '{% if r.status == \'excluida\' %}disabled{% endif %}>'
    line += '<label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_' + nome_modulo + '">' + label + '</label>'
    if descricao:
        line += '<div class="small text-muted">' + descricao + '</div>'
    line += '</div>'
    # Adicionar newline no final
    seletor_lines.append(line)

# Definição dos módulos: (chave_jinja, label_exibicao, descricao_curta)
# Ordem: conforme menu lateral, propostas têm grupo próprio
modulos_definicoes = [
    # Cadastros
    ('entidades', 'Entidades', 'Clientes, fornecedores e vendedores'),
    ('fluxo', 'Fluxo Caixa', 'Movimentação de caixa'),
    ('contas_banco', 'Contas Banco', 'Gestão de contas bancárias'),
    # Mercadoria
    ('comercial', 'Comercial', 'PDV, NF-e, NFC-e e Pedidos'),
    ('estoque', 'Estoque', 'Movimento de estoque'),
    ('compras', 'Compras', 'Entrada de NF de compra'),
    ('pedidos', 'Pedidos', 'Pedidos de venda'),
    ('pdv', 'PDV', 'PDV Caixa'),
    # Propostas - grupo próprio (como no menu)
    ('propostas', 'Propostas Comerciais', 'Gestão de propostas comerciais'),
    ('aprovacao', 'Aprovação de Propostas', 'Aprovação de propostas'),
    # Serviços / Fiscal
    ('servicos', 'Serviços / Fiscal', 'NFS-e e Importação de Notas'),
    # Locação
    ('locacao', 'Locação', 'Aluguel de Roupas e Fantasias'),
    # Contratos
    ('contratos', 'Contratos', 'Gestão de Contratos de Serviços'),
    # Financeiro
    ('financeiro', 'Financeiro', 'Gestão Financeira e Fluxo de Caixa'),
    # Relatórios
    ('relatorios', 'Relatórios', 'Relatórios gerenciais e fiscais'),
    # Admin
    ('usuarios', 'Usuários', 'Gerenciar Usuários'),
    ('controle_acesso', 'Controle de Acesso', 'Controle de Acesso'),
]

# Adicionar checkboxes organizados por categorias
# As categorias definem agrupamento visual, mas os checkboxes fluem em grade 4 por linha
categorias_ordem = [
    ('Cadastros', ['entidades', 'fluxo', 'contas_banco']),
    ('Mercadoria', ['comercial', 'estoque', 'compras', 'pedidos', 'pdv']),
    ('Propostas', ['propostas', 'aprovacao']),
    ('Serviços / Fiscal', ['servicos']),
    ('Locação', ['locacao']),
    ('Contratos', ['contratos']),
    ('Financeiro', ['financeiro']),
    ('Relatórios', ['relatorios']),
    ('Admin', ['usuarios', 'controle_acesso']),
]

posicao = 0
for cat_nome, chaves in categorias_ordem:
    # Pequena indicação de categoria - comentário, sem h6 full-width
    seletor_lines.append('            <!-- ' + cat_nome + ' -->')
    for chave in chaves:
        # Encontrar definição
        definicao = None
        for d in modulos_definicoes:
            if d[0] == chave:
                definicao = d
                break
        if definicao:
            nome_mod, label, desc = definicao
            add_checkbox_line(nome_mod, label, desc)
    posicao += len(chaves)

# Juntar todas as linhas com newline entre elas
conteudo_seletor = '\n'.join(seletor_lines)
# Garantir que termina com newline
if not conteudo_seletor.endswith('\n'):
    conteudo_seletor += '\n'

if inicio_seletor is not None and fim_seletor is not None:
    novas_linhas = linhas[:inicio_seletor+1]
    novas_linhas.append(conteudo_seletor)
    novas_linhas.extend(linhas[fim_seletor:])
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(novas_linhas)
    print('Seletor reescrito com grade 4 por linha e propostas próprias aplicado')
    print(f'Total de itens adicionados: {posicao}')
else:
    print('ERRO: não encontrou os marcadores')