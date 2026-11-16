from html.parser import HTMLParser
from pathlib import Path
import importlib.util
from jinja2 import Environment

ROOT=Path(__file__).resolve().parents[1]


class Forms(HTMLParser):
    def __init__(self):
        super().__init__();self.contract=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('form','input','select','button','textarea','option'):
            self.contract.append((tag,tuple((k,v) for k,v in attrs if k!='class')))


def test_theme_adjustment_preserves_forms_and_is_idempotent():
    spec=importlib.util.spec_from_file_location('theme_adjust',ROOT/'scripts/ajustar_tema_central_backoffice.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for relative in module.FILES:
        source=(ROOT/'src/templates'/relative).read_text(encoding='utf-8')
        transformed=module.transform(source)
        before,after=Forms(),Forms();before.feed(source);after.feed(transformed)
        assert before.contract==after.contract
        assert source==transformed
        assert 'class="card ' not in source
        assert 'central-backoffice.css' in source
        Environment().parse(source)


def test_css_is_scoped_and_uses_original_theme_tokens():
    css=(ROOT/'src/static/css/central-backoffice.css').read_text(encoding='utf-8')
    assert '--ls-input-bg' in css and '--ls-text-main' in css
    assert '--ls-page-title' in css
    assert 'data-theme="bluemetal"' in css and 'data-theme="moonlight"' in css
    assert 'body {' not in css and ':root {' not in css