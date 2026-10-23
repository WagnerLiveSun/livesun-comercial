#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[460:510], start=461):
        print(f"{i}: {line.rstrip()}")