from src.app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        from src.models import NfseServicoNacionalReferencia
        items = NfseServicoNacionalReferencia.query.filter_by(ativo=True).limit(20).all()
        for it in items:
            print(it.codigo_tributacao_nacional, '-', (it.descricao or '').strip()[:120])
