import re

with open('src/templates/admin/comercial_panel.html','r',encoding='utf-8') as f:
    content = f.read()

# Remove remaining category blocks: Mercadoria, Contratos, Financeiro, Relatorios, Admin
categories = ['Mercadoria', 'Contratos', 'Financeiro', 'Relatorios', 'Admin']

for cat in categories:
    pattern = rf'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">{cat}</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    if new_content != content:
        content = new_content
        print(f'Removed: {cat}')

with open('src/templates/admin/comercial_panel.html','w',encoding='utf-8') as f:
    f.write(content)

print('Done removing all category blocks')