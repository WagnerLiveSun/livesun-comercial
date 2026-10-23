#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to find and replace the first "Comercial" group (with proposals) 
# and remove the second "Comercial" group

# The current structure has:
# - First "Comercial" at line ~467 with the original items
# - Second "Comercial" at line ~497 with the proposal functions

# We want:
# - ONE "Comercial" group with proposals FIRST, then the other items

# Let's find the positions
import re

# Find all "Comercial" groups
matches = list(re.finditer(r"'(Comercial)'.+?'\]", content, re.DOTALL))
print(f"Found {len(matches)} 'Comercial' groups")

# The first group starts at match[0].start(), the second at match[1].start()
if len(matches) >= 2:
    first_start = matches[0].start()
    second_start = matches[1].start()
    
    # We want to keep the first group but add proposals at the beginning
    # and remove the second group
    
    # Get the content between the first and second group
    between_content = content[first_start:second_start]
    
    # The new first group should have proposals at the beginning
    # followed by the original items
    
    # Extract the original items from the first group
    # The first group format: ('Comercial', [ items ])
    # We need to insert ('propostas', ...) and ('aprovacao', ...) at the start
    
    # Let's build the new first group
    # Find the items list [ ... ] in the first group
    first_group_bracket = content.index('[', first_start)
    first_group_close = content.index(']]', first_start) + 2
    
    items_content = content[first_group_bracket+1:first_group_close-2]
    
    # Build new group with proposals at the start
    new_first_group = """    ('Comercial',
        [
            ('propostas',
                'Propostas Comerciais',
                'Gestão de propostas comerciais'
            ),
            ('aprovacao',
                'Aprovação de Propostas',
                'Aprovação de propostas'
            ),
""" + items_content + """
        ]),"""
    
    # Now remove the second group
    # Find the second group and remove it
    second_group_start = second_start
    # Find the closing ]] of the second group
    second_group_close = content.index(']]', second_group_start) + 2
    
    # Replace the first group and remove the second
    new_content = content[:first_start] + new_first_group + content[second_group_close:]
    
    with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Structure fixed!")
else:
    print("Could not find two Comercial groups")