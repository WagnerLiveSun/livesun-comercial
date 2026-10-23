with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove hidden modulo_dashboard input line (LF line ending)
old = '<input type="hidden" name="modulo_dashboard" value="on">\n'
removed_count = content.count(old)
content = content.replace(old, '', 1)

with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print(f'Removed {removed_count} hidden modulo_dashboard lines')
print('Done!')

