#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the structure - the proposal items were inserted in the wrong place
# We need to move them inside the first Comercial group

old_structure = """    ('propostas',
                'Propostas Comerciais',
                'Gestão de propostas comerciais'
            ),
    ('aprovacao',
                'Aprovação de Propostas',
                'Aprovação de propostas'
            ),
        'Comercial',"""

new_structure = """    ('Comercial',
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

if old_structure in content:
    content = content.replace(old_structure, new_structure)
    with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Structure fixed!")
else:
    print("Old structure not found")