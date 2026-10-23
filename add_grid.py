import re

with open('src/templates/admin/comercial_panel.html','r',encoding='utf-8') as f:
    content = f.read()

# Insert grid after the "mb-4" div that contains the clientes table
# Find the closing </div> of the ls-card p-4 mb-4 and insert grid after it
marker = '</div>\n{% endblock %}'

grid_html = '''
<!-- Grid de Módulos 4 por Linha -->
<div class="row mb-4">
    <div class="col-12">
        <h5 class="mb-3 ls-page-title">Módulos</h5>
        <p class="text-muted mb-3">Painel sempre ativo</p>
        <div class="grid-modulos" id="modulosGrid">
            {% for r in rows %}
            <div class="ls-card p-3 h-100">
                <div class="modulo-title">
                    <span class="dashboards-badge" title="Sempre ativo">⟐</span>
                    {{ modulo_nome(r.modulos, r.empresa_id) }}
                </div>
                <div class="small text-muted modulo-desc">{{ modulo_desc(r.modulos, r.empresa_id) }}</div>
                <div class="mt-3">
                    {% set mod = r.modulos or {} %}
                    {% if r.status != 'excluida' %}
                    <!-- Entidades -->
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="modulo_entidades" id="mod_{{ r.empresa_id }}_entidades" {% if mod.get('entidades') %}checked{% endif %}{% if r.status == 'excluida' %}disabled{% endif %}>
                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_entidades">Entidades</label>
                    </div>
                    <!-- Fluxo de Caixa -->
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="modulo_fluxo" id="mod_{{ r.empresa_id }}_fluxo" {% if mod.get('fluxo') %}checked{% endif %}{% if r.status == 'excluida' %}disabled{% endif %}>
                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_fluxo">Fluxo Caixa</label>
                    </div>
                    <!-- Contas Banco -->
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="modulo_contas_banco" id="mod_{{ r.empresa_id }}_contas_banco" {% if mod.get('contas_banco') %}checked{% endif %}{% if r.status == 'excluida' %}disabled{% endif %}>
                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_contas_banco">Contas Banco</label>
                    </div>
                    <!-- Comercial -->
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="modulo_comercial" id="mod_{{ r.empresa_id }}_comercial" {% if mod.get('comercial') %}checked{% endif %}{% if r.status == 'excluida' %}disabled{% endif %}>
                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_comercial">Comercial</label>
                    </div>
                    <!-- Estoque -->
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="modulo_estoque" id="mod_{{ r.empresa_id }}_estoque" {% if mod.get('estoque') %}checked{% endif %}{% if r.status == 'excluida' %}disabled{% endif %}>
                        <label class="form-check-label small fw-semibold" for="mod_{{ r.empresa_id }}_estoque">Estoque</label>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>'''

# Insert before the {% endblock %}
new_content = content.replace(marker, grid_html + '\n' + marker)

with open('src/templates/admin/comercial_panel.html','w',encoding='utf-8') as f:
    f.write(new_content)

print('Grid inserted successfully')