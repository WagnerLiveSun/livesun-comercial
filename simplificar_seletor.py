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

seletor = []
seletor.append('            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">')

# Dashboard Gerencial - sempre ativo, fora do seletor de controle
seletor.append('            <div class="mb-3">')
seletor.append('                <div class="form-check form-switch disabled">')
seletor.append('                    <input class="form-check-input" type="checkbox" name="modulo_dashboard" id="mod_{{ r.empresa_id }}_dashboard" checked disabled>')
seletor.append('                    <label class="form-check-label small fw-semibold text-muted" for="mod_{{ r.empresa_id }}_dashboard">Dashboard Gerencial</label>')
seletor.append('                    <div class="small text-muted">Painel inicial do sistema <span class="text-success"><i class="fas fa-check-circle"></i> Sempre ativo</span></div>')
seletor.append('                </div>')
seletor.append('            </div>')

def grupo(titulo, items):
    linhas_grupo = []
    linhas_grupo.append('            <h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">' + titulo + '</h6>')
    linhas_grupo.append('            <div class="list-group list-group-flush mb-3">')
    for key, label, desc in items:
        linhas_grupo.append('                <div class="list-group-item list-group-item-action p-2">')
        linhas_grupo.append('                    <div class="form-check form-switch">')
        # Monta input corretamente
        linhas_grupo.append('                        <input class="form-check-input" type="checkbox" name="modulo_' + key + '" id="mod_{{ r.empresa_id }}_' + key + '" {% if r.modulos.get(\'' + key + '\') %}checked{% endif %}{% if r.status == \'excluida\' %}disabled{% endif %}>')
        linhas_grupo.append('                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_' + key + '">' + label + '</label>')
        linhas_grupo.append('                        <div class="small text-muted">' + desc + '</div>')
        linhas_grupo.append('                    </div>')
        linhas_grupo.append('                </div>')
    linhas_grupo.append('            </div>')
    return linhas_grupo

seletor.extend(grupo('Cadastros', [
    ('entidades', 'Entidades', 'Clientes, fornecedores e vendedores'),
    ('fluxo', 'Fluxo Caixa', 'Movimentação de caixa'),
    ('contas_banco', 'Contas Banco', 'Gestão de contas bancárias'),
]))

seletor.extend(grupo('Mercadoria', [
    ('comercial', 'Comercial', 'PDV, NF-e, NFC-e e Pedidos'),
    ('estoque', 'Estoque', 'Movimento de estoque'),
    ('compras', 'Compras', 'Entrada de NF de compra'),
    ('pedidos', 'Pedidos', 'Pedidos de venda'),
    ('pdv', 'PDV', 'PDV Caixa'),
]))

seletor.extend(grupo('Propostas', [
    ('propostas', 'Propostas Comerciais', 'Gestão de propostas comerciais'),
    ('aprovacao', 'Aprovação de Propostas', 'Aprovação de propostas'),
]))

seletor.extend(grupo('Serviços / Fiscal', [
    ('servicos', 'Serviços / Fiscal', 'NFS-e e Importação de Notas'),
]))

seletor.extend(grupo('Locação', [
    ('locacao', 'Locação', 'Aluguel de Roupas e Fantasias'),
]))

seletor.extend(grupo('Contratos', [
    ('contratos', 'Contratos', 'Gestão de Contratos de Serviços'),
]))

seletor.extend(grupo('Financeiro', [
    ('financeiro', 'Financeiro', 'Gestão Financeira e Fluxo de Caixa'),
]))

seletor.extend(grupo('Relatórios', [
    ('relatorios', 'Relatórios', 'Relatórios gerenciais e fiscais'),
]))

seletor.extend(grupo('Admin', [
    ('usuarios', 'Usuários', 'Gerenciar Usuários'),
    ('controle_acesso', 'Controle de Acesso', 'Controle de Acesso'),
]))

if inicio_seletor is not None and fim_seletor is not None:
    novas_linhas = linhas[:inicio_seletor+1]
    novas_linhas.append(''.join(seletor) + '\\n')
    novas_linhas.extend(linhas[fim_seletor:])
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(novas_linhas)
    print('Seletor simplificado aplicado com sucesso')
else:
    print('ERRO: não encontrou os marcadores')