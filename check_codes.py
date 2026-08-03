from src.app import app
from src.models import NfseCtribMunReferencia

with app.app_context():
    codes = NfseCtribMunReferencia.query.filter_by(codigo_ibge='3304557').filter(
        NfseCtribMunReferencia.codigo_tributacao_municipal.like('01.07%')
    ).limit(10).all()
    
    print("Códigos municipais do Rio de Janeiro (01.07):")
    for c in codes:
        print(f"{c.codigo_tributacao_municipal} - {c.descricao}")
