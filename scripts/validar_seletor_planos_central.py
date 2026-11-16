"""Executa JS real do Central em Chromium, sem bancos ou serviços externos."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]/'LiveSun_CentralControle/livesun-central'
script=(ROOT/'static/js/central.js').read_text(encoding='utf-8')
html='''<form id="new-subscription-form"><select name="produto_id"><option value="1">Propostas</option><option value="2">Comercial</option><option value="3">Sem plano</option></select><select name="plano_id"><option value="10" data-product="1">Propostas</option><option value="20" data-product="2">Básico</option><option value="21" data-product="2">Premium</option></select><small id="subscription-plan-feedback" hidden>Sem plano ativo</small><button id="create-subscription-button">Criar</button></form>'''
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page();page.set_content(html);page.add_script_tag(content=script)
    assert page.locator('[name=plano_id]').input_value()=='10'
    page.locator('[name=produto_id]').select_option('2')
    assert page.locator('[name=plano_id]').input_value()=='20'
    assert page.locator('option[value="20"]').is_enabled()
    assert page.locator('option[value="10"]').is_disabled()
    page.locator('[name=plano_id]').select_option('21')
    assert page.locator('[name=plano_id]').input_value()=='21'
    page.locator('[name=produto_id]').select_option('3')
    assert page.locator('[name=plano_id]').is_disabled()
    assert page.locator('#create-subscription-button').is_disabled()
    assert page.locator('#subscription-plan-feedback').is_visible()
    page.locator('[name=produto_id]').select_option('2')
    assert page.locator('[name=plano_id]').is_enabled()
    assert page.locator('#create-subscription-button').is_enabled()
    print('Chromium: troca de produto, habilitação dos planos, seleção e produto sem plano OK.')
    browser.close()