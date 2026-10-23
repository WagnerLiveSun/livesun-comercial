with open('src/templates/layout.html', 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

replacements = [
    ("show_filiais = has_activity('comercial') and has_permission('comercial_filiais')",
     "show_filiais = has_activity('entidades') and has_permission('comercial_filiais')"),
    ("show_produtos = has_activity('comercial') and has_permission('comercial_produtos')",
     "show_produtos = has_activity('entidades') and has_permission('comercial_produtos')"),
    ("show_servicos = has_activity('comercial') and has_permission('comercial_servicos')",
     "show_servicos = has_activity('entidades') and has_permission('comercial_servicos')"),
    ("show_estoque = has_activity('comercial') and has_permission('comercial_estoque')",
     "show_estoque = has_activity('estoque') and has_permission('comercial_estoque')"),
    ("show_compras = has_activity('comercial') and has_permission('comercial_compras')",
     "show_compras = has_activity('compras') and has_permission('comercial_compras')"),
    ("show_tabelas_preco = has_activity('comercial') and has_permission('comercial_tabelas_preco')",
     "show_tabelas_preco = has_activity('entidades') and has_permission('comercial_tabelas_preco')"),
    ("show_orcamentos = has_activity('comercial') and has_permission('comercial_orcamentos')",
     "show_orcamentos = has_activity('propostas') and has_permission('comercial_orcamentos')"),
    ("show_propostas_aprovacao = has_activity('comercial') and has_permission('comercial_orcamentos')",
     "show_propostas_aprovacao = has_activity('aprovacao') and has_permission('comercial_orcamentos')"),
    ("show_pedidos = has_activity('comercial') and has_permission('comercial_pedidos')",
     "show_pedidos = has_activity('pedidos') and has_permission('comercial_pedidos')"),
    ("show_pdv = has_activity('comercial') and has_permission('comercial_pdv')",
     "show_pdv = has_activity('pdv') and has_permission('comercial_pdv')"),
]

for old, new in replacements:
    if old not in content:
        print(f'WARNING: Could not find: {old[:60]}')
        changes.append(False)
    else:
        content = content.replace(old, new, 1)
        changes.append(True)

# Update show_comercial - remove propostas items
old_c = "{% set show_comercial = has_activity('comercial') and (show_filiais or show_produtos or show_servicos or show_estoque or show_compras or show_documentos or show_tabelas_preco or show_orcamentos or show_propostas_aprovacao or show_pedidos or show_pdv) %}"
new_c = "{% set show_comercial = has_activity('comercial') and (show_filiais or show_produtos or show_servicos or show_estoque or show_compras or show_documentos or show_tabelas_preco or show_pedidos or show_pdv) %}"
if old_c in content:
    content = content.replace(old_c, new_c, 1)
    changes.append(True)
else:
    print('WARNING: Could not find show_comercial')
    changes.append(False)

# Add show_propostas after show_comercial line
content = content.replace(
    new_c + '\n',
    new_c + '\n                 {% set show_propostas = (show_orcamentos or show_propostas_aprovacao) %}\n',
    1
)

# Rename Mercadoria -> Comercial in menu label
old_label = 'Mercadoria </div>'
new_label = 'Comercial</div>'
content = content.replace(old_label, new_label, 1)

with open('src/templates/layout.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print(f'Changes: {sum(changes)}/{len(changes)}')
