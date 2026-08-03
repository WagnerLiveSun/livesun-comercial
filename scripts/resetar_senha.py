import argparse

from src.app import create_app
from src.models import db, Empresa, User


def _normalize_document(value: str) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit())


def _find_empresa_by_document(cnpj_cpf: str):
    normalized = _normalize_document(cnpj_cpf)
    if not normalized:
        return None

    empresa = Empresa.query.filter_by(cnpj=normalized).first()
    if empresa:
        return empresa

    for candidate in Empresa.query.all():
        if _normalize_document(candidate.cnpj or "") == normalized:
            return candidate

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Reseta senha de usuario para um valor informado (padrao: admin123)."
    )
    parser.add_argument("--cnpj", help="CPF/CNPJ da empresa (opcional, recomendado se houver usuarios repetidos)")
    parser.add_argument("--username", help="Usuario de login")
    parser.add_argument("--email", help="Email do usuario")
    parser.add_argument("--senha", default="admin123", help="Nova senha (padrao: admin123)")
    args = parser.parse_args()

    if not args.username and not args.email:
        raise SystemExit("Informe --username ou --email para identificar o usuario.")

    app = create_app()
    with app.app_context():
        query = User.query

        if args.cnpj:
            empresa = _find_empresa_by_document(args.cnpj)
            if not empresa:
                raise SystemExit("Empresa nao encontrada para o CPF/CNPJ informado.")
            query = query.filter(User.empresa_id == empresa.id)

        if args.username:
            query = query.filter(db.func.lower(User.username) == args.username.strip().lower())

        if args.email:
            query = query.filter(db.func.lower(User.email) == args.email.strip().lower())

        users = query.all()

        if not users:
            raise SystemExit("Usuario nao encontrado com os filtros informados.")

        if len(users) > 1:
            print("Foram encontrados varios usuarios. Refine com --cnpj e/ou --email:")
            for user in users:
                empresa_nome = user.empresa.nome if user.empresa else "(sem empresa)"
                print(f"- id={user.id} empresa={empresa_nome} username={user.username} email={user.email}")
            raise SystemExit("Operacao cancelada para evitar reset indevido.")

        user = users[0]
        user.set_password(args.senha)
        db.session.commit()

        empresa_nome = user.empresa.nome if user.empresa else "(sem empresa)"
        print("Senha alterada com sucesso.")
        print(f"Usuario: {user.username} | Email: {user.email} | Empresa: {empresa_nome}")


if __name__ == "__main__":
    main()
