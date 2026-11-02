"""Integração manual local. Nunca transmite documentos ou consulta a SEFIN."""

import json
from datetime import date, datetime
from decimal import Decimal

from src.models import db, FluxoContaModel, Lancamento, NfseNacionalEmissao


def _data(valor):
    try:
        return date.fromisoformat(str(valor)[:10])
    except (ValueError, TypeError):
        return None


def integrar_emissao(empresa_id, emissao_id, usuario_id, obter_conta, obter_fluxo,
                    data_vencimento=None):
    """Confirma vínculo e lançamento numa transação, com bloqueio da emissão."""
    if empresa_id is None:
        raise ValueError("Empresa não identificada para integração.")
    emissao = NfseNacionalEmissao.query.filter_by(
        empresa_id=empresa_id, id=emissao_id,
    ).with_for_update().first()
    if emissao is None:
        raise ValueError("Nota não encontrada nesta empresa.")
    if emissao.situacao_fiscal != "AUTORIZADA" or emissao.cancelado_em or emissao.protocolo_cancelamento:
        raise ValueError("Somente notas autorizadas e não canceladas podem ser integradas.")
    if emissao.lancamento is not None:
        return {"status": "ja_integrada", "lancamento_id": emissao.lancamento.id}

    numero = emissao.numero_nfse
    if not numero:
        from xml.etree import ElementTree as ET
        from src.routes.nfse_nacional import _extrair_xml_nfse_do_payload
        xml = emissao.xml_nfse or _extrair_xml_nfse_do_payload(emissao.payload_retorno)
        try:
            raiz = ET.fromstring(xml or "")
            numero = next(((n.text or "").strip() for n in raiz.iter()
                           if n.tag.rsplit("}", 1)[-1] == "nNFSe" and n.text), None)
        except ET.ParseError:
            numero = None
    if not numero:
        raise ValueError("Número oficial não disponível no cadastro ou XML armazenado.")

    existentes = Lancamento.query.filter_by(
        empresa_id=empresa_id, numero_documento=numero, fonte="nfse_nacional",
    ).all()
    if len(existentes) > 1:
        raise ValueError("Há mais de um lançamento com este número. Confira os vínculos antes de integrar.")
    if existentes:
        lancamento = existentes[0]
        vinculo = NfseNacionalEmissao.query.filter_by(
            empresa_id=empresa_id, lancamento_id=lancamento.id,
        ).first()
        if vinculo or lancamento.entidade_id != emissao.tomador_id or lancamento.valor_real != emissao.valor_servico:
            raise ValueError("Lançamento existente incompatível ou vinculado a outra nota. Confira o financeiro.")
        status = "vinculada"
    else:
        conta = obter_conta(empresa_id)
        if conta is None:
            raise ValueError("Cadastre uma conta bancária para receber a NFS-e.")
        fluxo_id = emissao.tomador.fluxo_conta_id if emissao.tomador else None
        fluxo = FluxoContaModel.query.filter_by(
            empresa_id=empresa_id, id=fluxo_id, tipo="R",
        ).first() if fluxo_id else None
        if fluxo is None:
            fluxo_id = obter_fluxo(empresa_id)
        if not fluxo_id:
            raise ValueError("Fluxo de recebimento não disponível.")
        try:
            payload = json.loads(emissao.payload_envio or "{}")
        except (ValueError, TypeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        data_evento = _data(payload.get("data_emissao"))
        if data_evento is None and emissao.xml_dps:
            from xml.etree import ElementTree as ET
            try:
                raiz = ET.fromstring(emissao.xml_dps)
                data_evento = _data(next((n.text for n in raiz.iter()
                                         if n.tag.rsplit("}", 1)[-1] == "dhEmi"), None))
            except ET.ParseError:
                pass
        data_evento = data_evento or (emissao.criado_em.date() if emissao.criado_em else datetime.utcnow().date())
        vencimento = data_vencimento or _data(payload.get("data_vencimento")) or data_evento
        lancamento = Lancamento(
            empresa_id=empresa_id, entidade_id=emissao.tomador_id,
            conta_banco_id=conta.id, fluxo_conta_id=fluxo_id,
            data_evento=data_evento, data_vencimento=vencimento,
            data_pagamento=None, status="aberto", numero_documento=numero,
            valor_real=emissao.valor_servico, valor_pago=Decimal("0.00"),
            valor_imposto=emissao.valor_iss, valor_outros_custos=Decimal("0.00"),
            observacoes=emissao.observacoes or (emissao.servico.descricao if emissao.servico else ""),
            fonte="nfse_nacional",
        )
        db.session.add(lancamento)
        db.session.flush()
        status = "criada"
    emissao.numero_nfse = numero
    emissao.lancamento = lancamento
    emissao.log_tecnico = (emissao.log_tecnico or "") + (
        f"\nIntegração financeira manual: usuário {usuario_id}, lançamento {lancamento.id}, "
        f"{datetime.utcnow().isoformat()} UTC, {status}."
    )
    return {"status": status, "lancamento_id": lancamento.id}