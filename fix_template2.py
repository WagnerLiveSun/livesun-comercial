path = 'd:/App_LiveSun/LiveSun_Comercial_X/src/templates/admin/comercial_panel.html'
with open(path, encoding='utf-8') as f:
    lines = f.read().split('\n')

# locate the log card row
i_row = None
for i in range(len(lines)):
    if lines[i].strip() == '<div class="row g-4">' and i+2 < len(lines):
        if lines[i+1].strip() == '<div class="col-lg-6">' and lines[i+2].strip() == '<div class="ls-card p-4 h-100">':
            i_row = i
            break
assert i_row is not None, 'row not found'

i_next_col = None
for i in range(i_row+1, len(lines)):
    if lines[i].strip() == '<div class="col-lg-6">':
        i_next_col = i
        break
assert i_next_col is not None, 'next col not found'
i_close_col = i_next_col - 1

new_col = r'''<div class="ls-card p-4 h-100">
    <h5 class="mb-3 ls-page-title"><i class="fas fa-info-circle me-2"></i>Log de Eventos</h5>
    <p class="text-muted small mb-3">
        Eventos auditáveis registrados pelo backoffice comercial (usuário, data/hora,
        categoria e tipo). Use os filtros abaixo para restringir a visualização.
    </p>
    <form method="GET" class="d-flex flex-wrap gap-2 mb-3">
        <input type="text" name="categoria" value="{{ filtros.get('categoria', '') }}"
               class="form-control form-control-sm" placeholder="Filtrar por categoria">
        <input type="text" name="tipo" value="{{ filtros.get('tipo', '') }}"
               class="form-control form-control-sm" placeholder="Filtrar por tipo">
        <button type="submit" class="btn btn-sm btn-outline-primary">Filtrar</button>
        <a href="{{ url_for('admin_comercial.index') }}" class="btn btn-sm btn-outline-secondary">Limpar</a>
    </form>
    <div class="table-responsive">
        <table class="table table-hover align-middle ls-theme-table mb-0">
            <thead>
                <tr>
                    <th>Quando</th>
                    <th>Usuário</th>
                    <th>Empresa</th>
                    <th>Categoria</th>
                    <th>Tipo</th>
                    <th>Descrição</th>
                </tr>
            </thead>
            <tbody>
                {% for e in eventos %}
                <tr>
                    <td>{{ e.criado_em.strftime('%d/%m/%Y %H:%M:%S') if e.criado_em else '-' }}</td>
                    <td>{{ e.usuario_id or '-' }}</td>
                    <td>{{ e.empresa_id or '-' }}</td>
                    <td class="text-center"><span class="badge {% if e.categoria == 'sucesso' %}bg-success{% elif e.categoria == 'alerta' %}bg-warning text-dark{% elif e.categoria == 'erro' %}bg-danger{% else %}bg-secondary{% endif %}">{{ e.categoria }}</span></td>
                    <td>{{ e.tipo }}</td>
                    <td class="text-truncate" style="max-width:260px;" title="{{ e.descricao or '' }}">{{ e.descricao or '-' }}</td>
                </tr>
                {% else %}
                <tr><td colspan="6" class="text-muted">Nenhum evento registrado.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
'''.split('\n')

if new_col and new_col[0] == '':
    new_col = new_col[1:]

lines[i_row+2 : i_close_col] = new_col

with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('LOG_CARD_REPLACED')
