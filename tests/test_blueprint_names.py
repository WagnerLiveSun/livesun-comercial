"""Detecta nomes de blueprint corrompidos sem inicializar banco ou aplicação."""

import ast
from pathlib import Path


def test_nomes_de_blueprints_nao_contem_anotacoes_de_arquivo():
    raiz = Path(__file__).resolve().parents[1] / "src" / "routes"
    encontrados = {}
    for arquivo in raiz.glob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8-sig"))
        for node in ast.walk(arvore):
            if not isinstance(node, ast.Call):
                continue
            nome = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if nome != "Blueprint" or not node.args:
                continue
            argumento = node.args[0]
            if isinstance(argumento, ast.Constant) and isinstance(argumento.value, str):
                valor = argumento.value
                assert valor and "." not in valor, f"Nome inválido em {arquivo}:{node.lineno}: {valor}"
                assert " - " not in valor, f"Anotação indevida em {arquivo}:{node.lineno}: {valor}"
                encontrados[arquivo.name] = valor
    assert encontrados["comercial_operacional.py"] == "comercial_operacional"


def test_blueprint_comercial_pode_ser_registrado():
    from flask import Flask
    from src.routes.comercial_operacional import comercial_bp

    app = Flask(__name__)
    app.register_blueprint(comercial_bp)
    assert app.blueprints["comercial_operacional"] is comercial_bp