#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
try:
    with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Propostas section
    idx = content.find("'Propostas'")
    if idx >= 0:
        print("=== Propostas GROUP FOUND ===")
        print(content[idx:idx+200])
    else:
        print("=== Propostas GROUP NOT FOUND ===")
    
    # Find Mercadoria section
    idx2 = content.find("'Mercadoria'")
    if idx2 >= 0:
        print("=== Mercadoria GROUP FOUND ===")
        print(content[idx2:idx2+200])
    else:
        print("=== Mercadoria GROUP NOT FOUND ===")
except Exception as e:
    print(f"Error: {e}")