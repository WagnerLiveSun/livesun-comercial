"""Integração financeira manual, sem comunicação com a SEFIN."""
import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from src.models import db, Entidade, NfseNacionalEmissao
from src.tenant import scoped_query, tenant_id
from src.routes.nfse_nacional import (
    nfse_nacional_bp, _date_from_request,
    _get_or_create_conta_banco_principal, _get_or_create_fluxo_recebimento,
)
from src.services.nfse_financeiro import integrar_emissao


@nfse_nacional_bp.route("/integracao-financeira", methods=["GET", "POST"])
@login_required
def integracao_financeira():
    resultados = []
    if request.method == "POST":
        ids = list(dict.fromkeys(request.form.getlist("emissao_ids")))
        texto = request.form.get("data_vencimento", "").strip()
        vencimento = _date_from_request(texto)
        if not ids or len(ids) > 100 or (texto and not vencimento):
            flash("Selecione de 1 a 100 notas e informe um vencimento válido, se preenchido.", "warning")
            return redirect(url_for("nfse_nacional.integracao_financeira"))
        for identificador in ids:
            try:
                resultado = integrar_emissao(
                    tenant_id(), int(identificador), current_user.id,
                    _get_or_create_conta_banco_principal, _get_or_create_fluxo_recebimento,
                    data_vencimento=vencimento,
                )
                db.session.commit()
                resultados.append({"emissao_id": identificador, **resultado})
            except Exception as exc:
                db.session.rollback()
                logging.exception("Falha na integração financeira manual da emissão %s", identificador)
                mensagem = str(exc) if isinstance(exc, ValueError) else "Falha ao gravar no financeiro. Consulte os logs."
                resultados.append({"emissao_id": identificador, "status": "erro", "mensagem": mensagem})

    situacao = request.args.get("situacao", "pendentes")
    if situacao not in ("pendentes", "processadas", "todas"):
        situacao = "pendentes"
    busca = request.args.get("busca", "").strip()
    base = scoped_query(NfseNacionalEmissao)
    autorizadas = db.and_(
        NfseNacionalEmissao.situacao_fiscal == "AUTORIZADA",
        NfseNacionalEmissao.cancelado_em.is_(None),
        NfseNacionalEmissao.protocolo_cancelamento.is_(None),
    )
    pendentes = base.filter(autorizadas, ~NfseNacionalEmissao.lancamento.has())
    processadas = base.filter(NfseNacionalEmissao.lancamento.has())
    total_pendentes, total_processadas = pendentes.count(), processadas.count()
    query = pendentes if situacao == "pendentes" else processadas
    if situacao == "todas":
        query = base.filter(db.or_(NfseNacionalEmissao.lancamento.has(), autorizadas))
    if busca:
        query = query.join(Entidade, NfseNacionalEmissao.tomador).filter(db.or_(
            NfseNacionalEmissao.numero_nfse.ilike(f"%{busca}%"),
            NfseNacionalEmissao.numero_interno.ilike(f"%{busca}%"),
            Entidade.nome.ilike(f"%{busca}%"),
        ))
    pagination = query.order_by(NfseNacionalEmissao.criado_em.desc()).paginate(
        page=request.args.get("page", 1, type=int), per_page=50, error_out=False,
    )
    return render_template(
        "nfse_nacional/integracao_financeira.html", pagination=pagination,
        situacao=situacao, busca=busca, resultados=resultados,
        total_pendentes=total_pendentes, total_processadas=total_processadas,
    )