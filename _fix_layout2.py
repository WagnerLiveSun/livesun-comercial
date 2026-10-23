with open('src/templates/layout.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove Propostas items from Comercial group, add separate Propostas group
old_menu = '''                    {% if show_pdv %}<li><a class="ls-sidebar-link {% if request.endpoint and request.endpoint.startswith('comercial_operacional.pdv') %}active{% endif %}" href="{{ url_for('comercial_operacional.pdv_index') }}"><i class="fas fa-cash-register"></i> PDV Caixa</a></li>{% endif %}
                    {% if show_orcamentos %}<li><a class="ls-sidebar-link {% if request.endpoint and request.endpoint.startswith('comercial_operacional.orcamentos') %}active{% endif %}" href="{{ url_for('comercial_operacional.orcamentos_index') }}"><i class="fas fa-file-invoice-dollar"></i> Propostas Comerciais</a></li>{% endif %}
                    {% if show_propostas_aprovacao %}<li><a class="ls-sidebar-link {% if request.endpoint == 'comercial_operacional.propostas_aprovacao' %}active{% endif %}" href="{{ url_for('comercial_operacional.propostas_aprovacao') }}"><i class="fas fa-clipboard-check"></i> Aprovação de Propostas</a></li>{% endif %}
                </ul>
                {% endif %}'''

new_menu = '''                    {% if show_pdv %}<li><a class="ls-sidebar-link {% if request.endpoint and request.endpoint.startswith('comercial_operacional.pdv') %}active{% endif %}" href="{{ url_for('comercial_operacional.pdv_index') }}"><i class="fas fa-cash-register"></i> PDV Caixa</a></li>{% endif %}
                </ul>
                {% endif %}

                {% if show_propostas %}
                <div class="ls-sidebar-section-label"><i class="fas fa-file-invoice-dollar"></i> Propostas</div>
                <ul class="ls-sidebar-nav">
                    {% if show_orcamentos %}<li><a class="ls-sidebar-link {% if request.endpoint and request.endpoint.startswith('comercial_operacional.orcamentos') %}active{% endif %}" href="{{ url_for('comercial_operacional.orcamentos_index') }}"><i class="fas fa-file-invoice-dollar"></i> Propostas Comerciais</a></li>{% endif %}
                    {% if show_propostas_aprovacao %}<li><a class="ls-sidebar-link {% if request.endpoint == 'comercial_operacional.propostas_aprovacao' %}active{% endif %}" href="{{ url_for('comercial_operacional.propostas_aprovacao') }}"><i class="fas fa-clipboard-check"></i> Aprovação de Propostas</a></li>{% endif %}
                </ul>
                {% endif %}'''

if old_menu in content:
    content = content.replace(old_menu, new_menu, 1)
    with open('src/templates/layout.html', 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('Menu restructured: Propostas moved to separate group')
else:
    print('ERROR: old_menu not found')
