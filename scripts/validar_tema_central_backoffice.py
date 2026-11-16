"""Verificação visual isolada em Chromium, sem login, banco ou requisições externas."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
layout=(ROOT/'src/templates/layout.html').read_text(encoding='utf-8')
styles='\n'.join(re.findall(r'<style>(.*?)</style>',layout,re.S))
css=(ROOT/'src/static/css/style.css').read_text(encoding='utf-8')
scoped=(ROOT/'src/static/css/central-backoffice.css').read_text(encoding='utf-8')
html='<html><head><style>'+css+styles+scoped+'</style></head><body><main class="central-backoffice"><section class="ls-card"><h1>Conectar ao Central</h1><label>Empresa<input class="form-control ls-theme-control" value="Empresa de teste"></label><select class="form-select ls-theme-control"><option>Empresa</option></select><button class="btn ls-btn-primary">Vincular</button></section></main></body></html>'

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.set_content(html)
    for theme in ('moonlight','bluemetal','sunset'):
        page.evaluate('(theme)=>{document.documentElement.dataset.theme=theme;document.body.dataset.theme=theme}',theme)
        actual=page.locator('input').evaluate('(e)=>({bg:getComputedStyle(e).backgroundColor,fg:getComputedStyle(e).color})')
        expected=page.evaluate('()=>getComputedStyle(document.documentElement).getPropertyValue("--ls-text-main").trim()')
        text=page.locator('input').evaluate('(e)=>{const a=document.createElement("span");a.style.color=getComputedStyle(document.documentElement).getPropertyValue("--ls-text-main");document.body.append(a);const c=getComputedStyle(a).color;a.remove();return c}')
        assert actual['fg']==text,(theme,actual,expected)
        assert actual['bg']!='rgb(255, 255, 255)' if theme=='moonlight' else True
        assert page.locator('input').is_visible() and page.locator('button').is_visible()
        print(theme+': campos e cores do tema original OK; '+str(actual))
    browser.close()