import re

with open('src/templates/admin/comercial_panel.html','r',encoding='utf-8') as f:
    content = f.read()

# Remove the "Cadastros" h6 + list-group-flush block
# Match from h6 through the closing </div> of list-group-flush
pattern = r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>\s*<div class="list-group list-group-flush mb-3">[^<]*(?:<div[^>]*>[^<]*</div>[^<]*)*</div>'

new_content = re.sub(pattern, '', content, flags=re.DOTALL)

if new_content == content:
    print('Pattern 1 not matched, trying alternative...')
    # Try simpler pattern - just remove up to next h6 or end
    # Find the Cadastros h6 and remove until the next h6 or end
    idx = new_content.find('<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>')
    if idx >= 0:
        # Find the next h6 after this one
        next_h6 = new_content.find('<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">', idx + 50)
        if next_h6 >= 0:
            new_content = new_content[:idx] + new_content[next_h6:]
        else:
            new_content = new_content[:idx]
    
with open('src/templates/admin/comercial_panel.html','w',encoding='utf-8') as f:
    f.write(new_content)

print('Done. Removed Cadastros block')