import re
with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    c = f.read()
print('File length:', len(c))
form_start = c.find('<form method="POST" action="{{ url_for(')
print('form_start:', form_start)
if form_start >= 0:
    form_end = c.find('</form>', form_start)
    print('form_end:', form_end)
    if form_end >= 0:
        form_section = c[form_start:form_end]
        print('form_section length:', len(form_section))
        print('h6 in form_section:', '<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>' in form_section)
        print('list-group in form_section:', '<div class="list-group list-group-flush mb-3">' in form_section)
        old_h6 = '<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">Cadastros</h6>'
        old_list = '<div class="list-group list-group-flush mb-3">'
        if old_h6 in form_section:
            form_section = form_section.replace(old_h6, '')
            print('Removed h6 from form_section')
        if old_list in form_section:
            form_section = form_section.replace(old_list, '')
            print('Removed list-group from form_section')
        c = c[:form_start] + form_section + c[form_end+7:]
        print('New file length:', len(c))
with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')