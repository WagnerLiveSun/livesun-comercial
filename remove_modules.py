import re

with open('src/templates/admin/comercial_panel.html','r',encoding='utf-8') as f:
    content = f.read()

# Remove all h6 + list-group-flush blocks
patterns_to_remove = [
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Mercadoria</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Contratos</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Financeiro</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Relatorios</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
    (r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Admin</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>', ''),
]

for pattern, replacement in patterns_to_remove:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('src/templates/admin/comercial_panel.html','w',encoding='utf-8') as f:
    f.write(content)

print('Removido com sucesso')