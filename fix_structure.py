#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the first Comercial group to include proposals
old_group = """    ('Comercial',
        [
            ('comercial',
                'Comercial',
                'PDV, NF-e, NFC-e e Pedidos'
            ),
            ('estoque',
                'Estoque',
                'Movimento de estoque'
            ),
            ('compras',
                'Compras',
                'Entrada de NF de compra'
            ),
            ('pedidos',
                'Pedidos',
                'Pedidos de venda'
            ),
            ('pdv',
                'PDV',
                'PDV Caixa'
            ),
        ]),"""

new_group = """    ('Comercial',
        [
            ('propostas',
                'Propostas Comerciais',
                'Gestão de propostas comerciais'
            ),
            ('aprovacao',
                'Aprovação de Propostas',
                'Aprovação de propostas'
            ),
            ('comercial',
                'Comercial',
                'PDV, NF-e, NFC-e e Pedidos'
            ),
            ('estoque',
                'Estoque',
                'Movimento de estoque'
            ),
            ('compras',
                'Compras',
                'Entrada de NF de compra'
            ),
            ('pedidos',
                'Pedidos',
                'Pedidos de venda'
            ),
            ('pdv',
                'PDV',
                'PDV Caixa'
            ),
        ]),"""

if old_group in content:
    content = content.replace(old_group, new_group)
    with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Substitution successful!")
else:
    print("Old group not found in content")
    # Print what's around line 467 for debugging
    lines = content.split('\n')
    for i, line in enumerate(lines[466:510], start=467):
        print(f"{i}: {line}")