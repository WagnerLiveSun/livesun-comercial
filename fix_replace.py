import re
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    c = f.read()
form_start = c.find('<form method="POST" action="{{ url_for(')
if form_start >= 0:
    form_end = c.find('</form>', form_start)
    if form_end >= 0:
        form_section = c[form_start:form_end]
        old_h6 = '<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>'
        old_list = '<div class="list-group list-group-flush mb-3">'
        if old_h6 in form_section:
            form_section = form_section.replace(old_h6, '')
        if old_list in form_section:
            form_section = form_section.replace(old_list, '')
        c = c[:form_start] + form_section + c[form_end+7:]
with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')