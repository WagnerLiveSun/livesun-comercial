#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The current structure has proposal items before 'Comercial', [
# We need to move them INSIDE the group
# Current (wrong):
#     ('propostas', ...)
#     ('aprovacao', ...)
#         'Comercial',
#     [
# We need:
# ('Comercial',
# [
#     ('propostas', ...),
#     ('aprovacao', ...),
#     ('comercial', ...),
#     ...

# Find the position of 'Comercial', 
comercial_pos = None
for i, line in enumerate(lines):
    if "'Comercial'," in line and i > 460 and i < 500:
        comercial_pos = i
        break

if comercial_pos:
    # Remove the proposal items from their current position (lines 467-474)
    # and insert them inside the group after 'Comercial', [
    # First, let's find where to insert
    
    # Get the proposal lines (currently at 467-474, but 0-based indices 466-473)
    proposal_lines = lines[466:475]  # lines 467-475 (1-based)
    
    # Remove them from current position
    del lines[466:475]
    
    # Insert them after the 'Comercial', line
    # Find the 'Comercial', line
    comercial_line_idx = None
    for i, line in enumerate(lines):
        if "'Comercial'," in line and i > 460 and i < 500:
            comercial_line_idx = i
            break
    
    if comercial_line_idx:
        # Insert the proposal items after the 'Comercial', line
        # The proposal items should be: ('propostas', ...), ('aprovacao', ...),
        inserted_proposals = '''    ('propostas',
                'Propostas Comerciais',
                'Gestão de propostas comerciais'
            ),
    ('aprovacao',
                'Aprovação de Propostas',
                'Aprovação de propostas'
            ),'''
        lines.insert(comercial_line_idx + 1, inserted_proposals)
    
    with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Structure fixed!")
else:
    print("Could not find Comercial group position")