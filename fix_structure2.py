#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the first "Comercial" group (starts at line 467 with 'Comercial')
# and the second "Comercial" group (starts at line 497 with 'Comercial')
# We need to:
# 1. Add proposal functions to the first group
# 2. Remove the second group

# First, let's identify the structure
# Lines 467-494: First Comercial group (5+1 lines for the group marker and closing)
# Lines 496-510: Second Comercial group (need to remove)

# The first group ends at line 494 (the ]), and line 495 has "),"
# The second group starts at line 497 with 'Comercial'

# We'll insert the proposals at the beginning of the first group (after line 466)
# and remove lines 496-510 (the second group and its closing)

# Insert proposal functions after line 466 (which is the '),')
proposal_items = '''    ('propostas',
                'Propostas Comerciais',
                'Gestão de propostas comerciais'
            ),
    ('aprovacao',
                'Aprovação de Propostas',
                'Aprovação de propostas'
            ),'''

# Insert the proposal items after line 466
lines[466:466] = [proposal_items]

# Now remove the second group (lines 496-510, but adjusted for the inserted lines)
# After inserting 2 lines, the second group starts at line 497+2 = 499
# We need to remove lines 499-512 (the second group and its closing)
# The second group has: 'Comercial', [ ... ], so lines 497-510
# After insertion, it's at 499-512

# Let's remove lines 499-512 (indices 498-511 in 0-based)
del lines[498:512]  # adjusted for the 2 inserted lines

with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    
print("Structure fixed!")
print(f"Total lines: {len(lines)}")