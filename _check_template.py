with open('src/templates/admin/comercial_panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    <!-- Dashboard sempre ativo -->
                    <div class="modulos-dashboard">
                        <div class="form-check form-switch">
                            <input class="form-check-input"
                                   type="checkbox"
                                   name="modulo_dashboard"
                                   id="mod_{{ r.empresa_id }}_dashboard"
                                   checked
                                   disabled>

                            <label class="form-check-label small fw-semibold"
                                   for="mod_{{ r.empresa_id }}_dashboard">
                                Dashboard Gerencial
                            </label>

                            <div class="small text-muted">
                                Painel inicial do sistema
                            </div>
                        </div>

                        <span class="badge bg-success">
                            <i class="fas fa-check-circle me-1"></i>
                            Sempre ativo
                        </span>
                    </div>"""

new_block = """                    <!-- Dashboard (editável) -->
                    <div class="modulos-dashboard">
                        <div class="form-check form-switch">
                            <input class="form-check-input"
                                   type="checkbox"
                                   name="modulo_dashboard"
                                   id="mod_{{ r.empresa_id }}_dashboard"
                                   {% if mod.get('dashboard') %}checked{% endif %}>

                            <label class="form-check-label small fw-semibold"
                                   for="mod_{{ r.empresa_id }}_dashboard">
                                Dashboard Gerencial
                            </label>

                            <div class="small text-muted">
                                Painel inicial do sistema
                            </div>
                        </div>

                        {% if mod.get('dashboard') %}
                        <span class="badge bg-success">
                            <i class="fas fa-check-circle me-1"></i>
                            Ativo
                        </span>
                        {% else %}
                        <span class="badge bg-secondary">
                            <i class="fas fa-times-circle me-1"></i>
                            Inativo
                        </span>
                        {% endif %}
                    </div>"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    with open('src/templates/admin/comercial_panel.html', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Dashboard checkbox replaced successfully!')
else:
    print('ERROR: old_block not found in content')
    # Try to find partial matches
    for line in old_block.split('\n'):
        if line.strip() and line not in content:
            print(f'Missing line: {repr(line[:60])}')


