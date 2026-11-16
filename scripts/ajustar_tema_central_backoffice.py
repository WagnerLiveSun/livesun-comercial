"""Ajuste pontual de classes visuais; não modifica contratos dos formulários."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ('admin/central_setup.html', 'admin/central_modules.html', 'auth/central_subscription.html')


def transform(source):
    def replace_classes(match):
        classes = match.group(1).split()
        replacements = {'card': 'ls-card', 'btn-primary': 'ls-btn-primary',
                        'btn-outline-primary': 'ls-btn-secondary'}
        classes = [replacements.get(value, value) for value in classes]
        if ('form-control' in classes or 'form-select' in classes) and 'ls-theme-control' not in classes:
            classes.append('ls-theme-control')
        return 'class="' + ' '.join(classes) + '"'
    source = re.sub(r'class="([^"]*)"', replace_classes, source)
    source = source.replace('<input class="form-control ls-theme-control" name="confirmacao" type="checkbox"',
                            '<input class="form-check-input" name="confirmacao" type="checkbox"')
    source = source.replace('<input name="ativo" type="checkbox"', '<input class="form-check-input" name="ativo" type="checkbox"')
    source = source.replace('<input type="checkbox" name="modulo_', '<input class="form-check-input" type="checkbox" name="modulo_')
    source = source.replace('<div class="container py-4">', '<div class="container py-4 central-backoffice">', 1)
    if 'central-backoffice.css' not in source:
        marker = '{% block content %}'
        source = source.replace(marker, '{% block extra_css %}{{ super() }}<link rel="stylesheet" href="{{ url_for(\'static\',filename=\'css/central-backoffice.css\',v=\'1\') }}">{% endblock %}'+marker, 1)
    return source


if __name__ == '__main__':
    for relative in FILES:
        path = ROOT/'src/templates'/relative
        path.write_text(transform(path.read_text(encoding='utf-8')), encoding='utf-8')
        print(relative + ': classes de tema LiveSun aplicadas')