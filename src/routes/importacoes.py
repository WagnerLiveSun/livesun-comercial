import logging
"""
Rotas para importação de NFSe (Notas de Serviço) e OFX (Extratos Bancários)
"""

import os
# import zipfile # [REMOVER: suporte a compactados será desativado]
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from src.models import (
    db,
    ImportacaoNFSe,
    Entidade,
    FluxoContaModel,
    ContaBanco,
    Lancamento,
)
from src.services.ofx_parser import OFXParser
from src.services.conciliacao import criar_conciliacao_ofx, reconciliar_conciliacao

logger = logging.getLogger(__name__)


def _truncate_text(value: str | None, limit: int) -> str:
    text = (value or '').strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip()

# try:
#     import rarfile
#     HAS_RAR = True
# except ImportError:
#     HAS_RAR = False
#     rarfile = None

importacoes_bp = Blueprint('importacoes', __name__, url_prefix='/importacoes')

ALLOWED_EXTENSIONS = {'xml'}  # Removido zip e rar temporariamente


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extrair_namespace(root: ET.Element) -> dict:
    ns_str = root.tag.split('}')[0].strip('{')
    return {'n': ns_str} if ns_str else {}


def extrair_dados_nfse(xml_content: str):
    """
    Extrai os campos principais da NFSe no padrão nacional.
    Retorna (dados_dict, erro_str) – se erro_str != None, ocorreu erro.
    """
    try:
        tree = ET.ElementTree(ET.fromstring(xml_content))
        root = tree.getroot()
        ns = extrair_namespace(root)

        inf_nfse = root.find('.//n:infNFSe', ns)
        if inf_nfse is None:
            return None, 'XML não possui tag infNFSe (padrão nacional).'

        # 1. Tenta buscar campo padrão de alíquota ISS
        aliquota_iss = inf_nfse.findtext('.//n:pISSQN', default='', namespaces=ns)
        debug_origem = 'pISSQN'

        if not aliquota_iss or aliquota_iss.strip() in ('', '0', '0.0', '0,0'):
            aliquota_iss = inf_nfse.findtext('.//n:aliquotaISS', default='', namespaces=ns)
            debug_origem = 'aliquotaISS'

        if not aliquota_iss or aliquota_iss.strip() in ('', '0', '0.0', '0,0'):
            # 2. Busca global por pTotTribSN (Simples Nacional)
            p_tot_trib_sn_nodes = root.findall('.//n:pTotTribSN', ns)
            logging.debug(f"[DEBUG] Encontrados {len(p_tot_trib_sn_nodes)} pTotTribSN no XML: - importacoes.py:70")
            for idx, node in enumerate(p_tot_trib_sn_nodes):
                logging.debug(f"[DEBUG] pTotTribSN #{idx+1}: '{node.text}' - importacoes.py:72")
            if p_tot_trib_sn_nodes and p_tot_trib_sn_nodes[0].text:
                aliquota_iss = p_tot_trib_sn_nodes[0].text
                debug_origem = 'pTotTribSN-global'
            else:
                aliquota_iss = ''
                debug_origem = 'nenhum'

        # 3. Fallback: se ainda não achou alíquota, tenta extrair da descrição do serviço (xDescServ)
        if not aliquota_iss or aliquota_iss.strip() in ('', '0', '0.0', '0,0'):
            try:
                desc_serv = inf_nfse.findtext('.//n:xDescServ', default='', namespaces=ns)
                import re
                candidata = ''
                if desc_serv:
                    # Busca todos os números (com vírgula ou ponto) na descrição
                    matches = re.findall(r'[0-9]+[\.,][0-9]+', desc_serv)
                    # Percorre de trás para frente
                    for m in reversed(matches):
                        norm = m.replace(',', '.')
                        try:
                            v = float(norm)
                        except ValueError:
                            continue
                        if 0 < v <= 20:
                            candidata = norm
                            break
                if candidata:
                    aliquota_iss = candidata
                    debug_origem = 'fallback-xDescServ'
            except Exception as e:
                logging.debug(f"[DEBUG] Erro no fallback de xDescServ para alíquota ISS: {e} - importacoes.py:103")

        # 4. Se ainda não encontrou, usar padrão 6%
        if not aliquota_iss or aliquota_iss.strip() in ('', '0', '0.0', '0,0'):
            aliquota_iss = '6.0'
            debug_origem = 'padrao-6'

        logging.debug(f"[DEBUG] Alíquota ISS extraída: '{aliquota_iss}' (origem: {debug_origem}) - importacoes.py:110")

        dados = {
            'numero_nota': inf_nfse.findtext('n:nNFSe', default='', namespaces=ns),
            'data_emissao': inf_nfse.findtext('n:dhProc', default='', namespaces=ns),
            'cnpj_tomador': inf_nfse.findtext('n:DPS/n:infDPS/n:toma/n:CNPJ', default='', namespaces=ns),
            'valor_bruto_str': inf_nfse.findtext('n:valores/n:vLiq', default='', namespaces=ns),
            'descricao_servico': root.findtext('.//n:xDescServ', default='', namespaces=ns),
            'chave_nota': inf_nfse.get('Id') or '',
            'aliquota_iss_str': aliquota_iss,
            'debug_aliquota_iss_origem': debug_origem,
        }
        return dados, None
    except ET.ParseError:
        return None, 'XML inválido ou malformado.'
    except Exception as e:
        return None, f'Erro ao ler XML: {str(e)}'


def validar_dados_nfse(dados: dict):
    """
    Valida campos obrigatórios e converte valor_bruto_str para float em dados['valor_bruto'].
    Converte alíquota para float em dados['aliquota_iss'] e calcula dados['valor_iss'].
    Modifica o dict 'dados' in place.
    """
    campos_faltando = []

    if not dados.get('numero_nota'):
        campos_faltando.append('Número da Nota')
    if not dados.get('data_emissao'):
        campos_faltando.append('Data de Emissão')
    if not dados.get('cnpj_tomador'):
        campos_faltando.append('CNPJ do Tomador')

    # Valor bruto
    valor_bruto_str = dados.get('valor_bruto_str', '')
    try:
        dados['valor_bruto'] = float(valor_bruto_str.replace(',', '.')) if valor_bruto_str else 0.0
    except Exception:
        campos_faltando.append('Valor Líquido (inválido)')
        dados['valor_bruto'] = 0.0

    # Extrai e converte a alíquota do ISS
    import re
    aliquota_iss_str = dados.get('aliquota_iss_str', '').replace(',', '.').strip()
    # Remove espaços e caracteres não numéricos exceto ponto
    aliquota_iss_str = re.sub(r'[^0-9\.]', '', aliquota_iss_str)
    try:
        dados['aliquota_iss'] = float(aliquota_iss_str) if aliquota_iss_str else 0.0
    except Exception as e:
        logging.debug(f"[DEBUG] Erro ao converter aliquota_iss_str='{aliquota_iss_str}' para float: {e} - importacoes.py:160")
        dados['aliquota_iss'] = 0.0

    # Calcula o valor do ISS
    dados['valor_iss'] = round(dados['valor_bruto'] * dados['aliquota_iss'] / 100, 2)

    if campos_faltando:
        return False, f'Campos obrigatórios ausentes ou inválidos: {", ".join(campos_faltando)}.'

    return True, None


# Garante configuração do logger para DEBUG se não estiver configurado
def _configurar_logger_debug():
    logger = logging.getLogger()
    if not logger.hasHandlers():
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    else:
        logger.setLevel(logging.DEBUG)


_configurar_logger_debug()


def _get_or_create_default_fluxo_conta_id(empresa_id: int, tipo_movimentacao: str = 'R') -> int | None:
    """Obtém (ou cria) a conta de fluxo padrão por tipo para a empresa."""
    # Validação de segurança: garantir que o empresa_id corresponde ao usuário logado
    if empresa_id != getattr(current_user, 'empresa_id', None):
        logger.warning(f"Tentativa de acesso a conta de fluxo de empresa {empresa_id} pelo usuário {getattr(current_user, 'id', 'unknown')}")
        return None

    codigo_padrao = '1' if tipo_movimentacao == 'R' else '2'
    descricao_padrao = 'Entradas de Caixa' if tipo_movimentacao == 'R' else 'Saídas de Caixa'

    conta = (
        FluxoContaModel.query
        .filter_by(empresa_id=empresa_id, tipo=tipo_movimentacao, codigo=codigo_padrao)
        .order_by(FluxoContaModel.ativo.desc(), FluxoContaModel.id.asc())
        .first()
    )
    if conta:
        if not conta.ativo:
            conta.ativo = True
            db.session.flush()
        return conta.id

    # Compatibilidade com bases antigas que usavam outro código para padrão.
    conta_legada = (
        FluxoContaModel.query
        .filter_by(empresa_id=empresa_id, tipo=tipo_movimentacao, codigo='1.1.1')
        .order_by(FluxoContaModel.ativo.desc(), FluxoContaModel.id.asc())
        .first()
    )
    if conta_legada:
        if not conta_legada.ativo:
            conta_legada.ativo = True
            db.session.flush()
        return conta_legada.id

    conta = FluxoContaModel(
        empresa_id=empresa_id,
        codigo=codigo_padrao,
        descricao=descricao_padrao,
        tipo=tipo_movimentacao,
        nivel_sintetico=1,
        nivel_analitico=None,
        ativo=True,
    )
    db.session.add(conta)
    db.session.flush()
    if conta.id:
        return conta.id

    fallback = (
        FluxoContaModel.query
        .filter_by(empresa_id=empresa_id, ativo=True, tipo=tipo_movimentacao)
        .order_by(FluxoContaModel.codigo.asc(), FluxoContaModel.id.asc())
        .first()
    )
    return fallback.id if fallback else None


def _get_or_create_ofx_entidade_id(empresa_id: int, tipo_movimentacao: str) -> int:
    """Obtém (ou cria) uma entidade padrão para lançamentos vindos do OFX."""
    # Validação de segurança: garantir que o empresa_id corresponde ao usuário logado
    if empresa_id != getattr(current_user, 'empresa_id', None):
        logger.warning(f"Tentativa de acesso a entidade OFX de empresa {empresa_id} pelo usuário {getattr(current_user, 'id', 'unknown')}")
        raise ValueError('Acesso negado: empresa não corresponde ao usuário logado')

    cnpj_padrao = '00000000000000' if tipo_movimentacao == 'R' else '00000000000001'
    nome_padrao = 'Importação OFX - Créditos' if tipo_movimentacao == 'R' else 'Importação OFX - Débitos'
    tipo_entidade = 'C' if tipo_movimentacao == 'R' else 'F'

    entidade = Entidade.query.filter_by(
        empresa_id=empresa_id,
        cnpj_cpf=cnpj_padrao,
    ).first()

    if entidade:
        atualizou = False
        if entidade.nome != nome_padrao:
            entidade.nome = nome_padrao
            atualizou = True
        if entidade.tipo != tipo_entidade:
            entidade.tipo = tipo_entidade
            atualizou = True
        if not entidade.ativo:
            entidade.ativo = True
            atualizou = True
        if atualizou:
            db.session.flush()
        return entidade.id

    entidade = Entidade(
        empresa_id=empresa_id,
        nome=nome_padrao,
        cnpj_cpf=cnpj_padrao,
        tipo=tipo_entidade,
        ativo=True,
    )
    db.session.add(entidade)
    db.session.flush()
    return entidade.id


def _importar_ofx_com_lancamentos_diretos(empresa_id: int, conta_banco_id: int, ofx_content: str):
    """Cria lançamentos pagos diretamente a partir das transações do OFX, sem conciliação."""
    parser = OFXParser(ofx_content)
    if not parser.parse():
        raise ValueError('; '.join(parser.get_errors()) or 'Não foi possível processar o OFX.')

    transacoes = parser.get_transactions()
    if not transacoes:
        raise ValueError('Nenhuma transação encontrada no arquivo OFX.')

    importados = 0
    ignorados = 0

    for transacao in transacoes:
        referencia = (transacao.get('transaction_id') or transacao.get('referencia') or '').strip()
        data_movimento = transacao.get('data')
        valor = transacao.get('valor')

        if not data_movimento or valor is None:
            ignorados += 1
            continue

        if referencia:
            existe = Lancamento.query.filter_by(
                empresa_id=empresa_id,
                conta_banco_id=conta_banco_id,
                referencia_banco=referencia,
            ).first()
            if existe:
                ignorados += 1
                continue

        tipo_movimentacao = 'R' if float(valor) >= 0 else 'P'
        fluxo_conta_id = _get_or_create_default_fluxo_conta_id(empresa_id, tipo_movimentacao)
        if not fluxo_conta_id:
            raise ValueError(
                f'Não foi possível localizar/criar conta de fluxo padrão para tipo {tipo_movimentacao}. '
                'Cadastre uma conta de fluxo ativa e tente novamente.'
            )

        entidade_id = _get_or_create_ofx_entidade_id(empresa_id, tipo_movimentacao)
        descricao = _truncate_text(transacao.get('descricao') or 'Importação OFX', 1000)

        lancamento = Lancamento(
            empresa_id=empresa_id,
            data_evento=data_movimento,
            data_vencimento=data_movimento,
            data_pagamento=data_movimento,
            status='pago',
            entidade_id=entidade_id,
            fluxo_conta_id=fluxo_conta_id,
            conta_banco_id=conta_banco_id,
            valor_real=abs(float(valor)),
            valor_pago=abs(float(valor)),
            valor_imposto=0,
            valor_outros_custos=0,
            numero_documento=_truncate_text(referencia or '', 50) or None,
            observacoes=descricao,
            referencia_banco=referencia or None,
            fonte='ofx',
        )
        db.session.add(lancamento)
        importados += 1

    db.session.commit()
    return {
        'importados': importados,
        'ignorados': ignorados,
        'total': len(transacoes),
    }


def obter_ou_criar_entidade(empresa_id: int, cnpj_tomador: str):
    """
    Busca Entidade por CNPJ; se não existir, cria uma nova como Cliente.
    """
    # Validação de segurança: garantir que o empresa_id corresponde ao usuário logado
    if empresa_id != getattr(current_user, 'empresa_id', None):
        logger.warning(f"Tentativa de acesso a entidade de empresa {empresa_id} pelo usuário {getattr(current_user, 'id', 'unknown')}")
        return None, 'Acesso negado: empresa não corresponde ao usuário logado'

    entidade = Entidade.query.filter_by(empresa_id=empresa_id, cnpj_cpf=cnpj_tomador).first()
    if entidade:
        mudou = False
        if entidade.tipo != 'C':
            entidade.tipo = 'C'
            mudou = True

        if not entidade.fluxo_conta_id:
            fluxo_conta_id = _get_or_create_default_fluxo_conta_id(empresa_id, 'R')
            if fluxo_conta_id:
                entidade.fluxo_conta_id = fluxo_conta_id
                mudou = True

        if mudou:
            db.session.add(entidade)
            db.session.commit()
        return entidade, None

    try:
        fluxo_conta_id = _get_or_create_default_fluxo_conta_id(empresa_id, 'R')

        entidade = Entidade(
            empresa_id=empresa_id,
            tipo='C',
            nome=f'Tomador {cnpj_tomador}',
            cnpj_cpf=cnpj_tomador,
            ativo=True,
            fluxo_conta_id=fluxo_conta_id,
        )
        db.session.add(entidade)
        db.session.commit()
        return entidade, None
    except Exception as e:
        db.session.rollback()
        return None, f'Erro ao criar Entidade: {str(e)}'


def criar_lancamento_nfse(empresa_id: int, entidade: Entidade, dados: dict):
    """
    Cria um lançamento financeiro a partir dos dados da NFSe.
    """
    try:
        if not entidade.fluxo_conta_id:
            fluxo_conta_id = _get_or_create_default_fluxo_conta_id(empresa_id, 'R')
            if not fluxo_conta_id:
                return False, 'Não foi possível identificar/criar conta de fluxo padrão de Recebimento para a empresa.'
            entidade.fluxo_conta_id = fluxo_conta_id
            db.session.add(entidade)
            db.session.flush()

        data_emissao = dados.get('data_emissao', '')
        data_emissao_dt = None
        if data_emissao:
            try:
                data_emissao_dt = datetime.strptime(data_emissao[:10], '%Y-%m-%d').date()
            except Exception:
                data_emissao_dt = datetime.now(timezone.utc).date()

        conta_principal = ContaBanco.query.filter_by(empresa_id=empresa_id, is_principal=True).first()
        conta_banco_id = conta_principal.id if conta_principal else None

        from decimal import Decimal
        valor_imposto = dados.get('valor_iss', 0.0)
        if not isinstance(valor_imposto, Decimal):
            valor_imposto = Decimal(str(valor_imposto))

        lancamento = Lancamento(
            empresa_id=empresa_id,
            entidade_id=entidade.id,
            fluxo_conta_id=entidade.fluxo_conta_id,
            conta_banco_id=conta_banco_id,
            data_evento=data_emissao_dt,
            data_vencimento=data_emissao_dt,
            status='aberto',
            valor_real=dados.get('valor_bruto', 0.0),
            valor_pago=Decimal('0.00'),
            valor_imposto=valor_imposto,
            valor_outros_custos=Decimal('0.00'),
            numero_documento=dados.get('numero_nota') or dados.get('chave_nota'),
            observacoes=(dados.get('descricao_servico') or '').strip(),
        )
        db.session.add(lancamento)
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, f'Erro ao criar Lançamento: {str(e)}'


def _parse_date_from_nfse(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], '%Y-%m-%d').date()
    except Exception:
        return datetime.now(timezone.utc).date()


def processar_xml_nfse_completo(xml_content: str, empresa_id: int):
    """
    Processa o XML completo: extrai dados, valida, cria entidade (se preciso),
    cria lançamento e registro de ImportacaoNFSe.
    """
    dados, erro = extrair_dados_nfse(xml_content)
    if erro or not dados:
        return False, f'Erro ao extrair dados do XML: {erro or "dados não extraídos"}'

    try:
        # Ajusta chave_nota para deduplicação
        if not dados.get('chave_nota'):
            dados['chave_nota'] = f"{dados.get('numero_nota', '')}-{dados.get('cnpj_tomador', '')}"

        # Deduplicação
        existe = ImportacaoNFSe.query.filter_by(
            empresa_id=empresa_id,
            chave_nota=dados['chave_nota']
        ).first()
        if existe:
            return False, f'Nota já importada: {dados["chave_nota"]}'

        # Validação de campos + conversão de valor
        valido, erro_validacao = validar_dados_nfse(dados)
        if not valido:
            return False, erro_validacao

        # Entidade
        entidade, erro_entidade = obter_ou_criar_entidade(empresa_id, dados['cnpj_tomador'])
        if not entidade:
            return False, erro_entidade

        # Lançamento
        ok_lanc, erro_lanc = criar_lancamento_nfse(empresa_id, entidade, dados)
        if not ok_lanc:
            return False, erro_lanc

        # Registro de importação
        registro = ImportacaoNFSe(
            empresa_id=empresa_id,
            chave_nota=dados['chave_nota'],
            numero_nota=dados.get('numero_nota') or '',
            data_emissao=_parse_date_from_nfse(dados.get('data_emissao', '')),
            cnpj_tomador=dados.get('cnpj_tomador') or '',
            valor_bruto=dados.get('valor_bruto', 0.0),
            valor_impostos=None,
            descricao_servico=(dados.get('descricao_servico') or '').strip(),
            entidade_id=entidade.id,
            aliquota_iss=dados.get('aliquota_iss', 0.0),
        )
        db.session.add(registro)
        db.session.commit()
        return True, f'Nota importada: {dados["chave_nota"]}'
    except Exception as e:
        db.session.rollback()
        return False, f'Erro inesperado no processamento da NFSe: {_truncate_text(str(e), 255)}'


def processar_arquivo_nfse(file_path: str, empresa_id: int, mensagens: list):
    """
    Processa arquivo XML (compactados desativados temporariamente).
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.xml':
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        ok, msg = processar_xml_nfse_completo(xml_content, empresa_id)
        mensagens.append(msg)
    else:
        mensagens.append('Tipo de arquivo não suportado para processamento.')


@importacoes_bp.route('/nfse', methods=['GET', 'POST'])
@login_required
def importar_nfse():
    empresa_id = current_user.empresa_id

    if request.method == 'POST':
        # CONFIRMAÇÃO DO ESPELHO
        if 'confirmar' in request.form:
            numero_nota = request.form.get('numero_nota', '')
            data_emissao = request.form.get('data_emissao', '')
            cnpj_tomador = request.form.get('cnpj_tomador', '')
            valor_bruto_str = request.form.get('valor_bruto', '0').strip()
            descricao_servico = request.form.get('descricao_servico', '')
            chave_nota = request.form.get('chave_nota', '')

            # Conversão do valor bruto (string do formulário -> float)
            try:
                valor_bruto = float(valor_bruto_str.replace(',', '.')) if valor_bruto_str else 0.0
            except Exception:
                flash('Valor bruto inválido.', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            erros = []

            # Impedir duplicidade de chave_nota
            duplicado = ImportacaoNFSe.query.filter_by(
                empresa_id=empresa_id,
                chave_nota=chave_nota
            ).first()
            if duplicado:
                flash(f'Nota já importada: {chave_nota}', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Buscar ou criar entidade e garantir tipo 'C'
            entidade, erro_entidade = obter_ou_criar_entidade(empresa_id, cnpj_tomador)
            if not entidade:
                erros.append(erro_entidade or 'Entidade (cliente) não encontrada para o CNPJ informado. Cadastre a entidade antes de importar.')
            elif entidade.tipo != 'C':
                erros.append('Entidade encontrada, mas não é do tipo Cliente (C).')

            if entidade and not entidade.fluxo_conta_id:
                fluxo_padrao_id = _get_or_create_default_fluxo_conta_id(empresa_id, 'R')
                if fluxo_padrao_id:
                    entidade.fluxo_conta_id = fluxo_padrao_id
                    db.session.add(entidade)
                    db.session.flush()

            fluxo_conta_id = entidade.fluxo_conta_id if entidade else None
            if not fluxo_conta_id:
                erros.append('Entidade não possui conta de fluxo de caixa associada e não foi possível criar uma padrão de Recebimento.')

            # Conta bancária principal
            conta_principal = ContaBanco.query.filter_by(
                empresa_id=empresa_id,
                is_principal=True
            ).first()
            conta_banco_id = conta_principal.id if conta_principal else None
            if not conta_banco_id:
                erros.append('Empresa não possui conta bancária principal cadastrada.')

            if erros:
                for erro in erros:
                    flash(erro, 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Criar lançamento financeiro e associar entidade do tipo 'C'
            try:
                data_emissao_dt = None
                if data_emissao:
                    try:
                        data_emissao_dt = datetime.strptime(data_emissao[:10], '%Y-%m-%d').date()
                    except Exception:
                        data_emissao_dt = datetime.now(timezone.utc).date()

                from decimal import Decimal
                # Aceita tanto valor_imposto quanto valor_iss do formulário
                # Usar a alíquota do ISS do espelho para calcular o valor do imposto
                aliquota_iss_str = request.form.get('aliquota_iss')
                try:
                    aliquota_iss = float(str(aliquota_iss_str).replace(',', '.')) if aliquota_iss_str not in (None, '', 'None') else 0.0
                except Exception:
                    aliquota_iss = 0.0
                valor_imposto = Decimal(str(valor_bruto * aliquota_iss / 100)) if valor_bruto and aliquota_iss else Decimal('0.00')

                lancamento = Lancamento(
                    empresa_id=empresa_id,
                    entidade_id=entidade.id,
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco_id,
                    data_evento=data_emissao_dt,
                    data_vencimento=data_emissao_dt,
                    status='aberto',
                    valor_real=valor_bruto,
                    valor_pago=Decimal('0.00'),
                    valor_imposto=valor_imposto,
                    valor_outros_custos=Decimal('0.00'),
                    numero_documento=numero_nota or chave_nota,
                    observacoes=descricao_servico or '',
                )
                db.session.add(lancamento)
                db.session.flush()  # Garante que lancamento.id está disponível

                # Registro de importação vinculado ao lançamento
                registro = ImportacaoNFSe(
                    empresa_id=empresa_id,
                    chave_nota=chave_nota,
                    numero_nota=numero_nota or '',
                    data_emissao=data_emissao_dt,
                    cnpj_tomador=cnpj_tomador or '',
                    valor_bruto=valor_bruto,
                    valor_impostos=None,
                    descricao_servico=descricao_servico or '',
                    entidade_id=entidade.id,
                    lancamento_id=lancamento.id,
                    aliquota_iss=aliquota_iss,
                )
                db.session.add(registro)
                db.session.commit()
                flash(f'Nota importada: {chave_nota}', 'info')
                return redirect(url_for('importacoes.importar_nfse'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar Lançamento/Registro: {str(e)}', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

        # UPLOAD DO XML PARA ESPELHO
        if 'file' not in request.files:
            flash('Nenhum arquivo foi enviado.', 'danger')
            return redirect(url_for('importacoes.importar_nfse'))

        arquivo = request.files['file']
        if not arquivo or arquivo.filename == '':
            flash('Selecione um arquivo XML.', 'danger')
            return redirect(url_for('importacoes.importar_nfse'))

        if not allowed_file(arquivo.filename):
            flash('Formato inválido. Envie um arquivo .xml', 'warning')
            return redirect(url_for('importacoes.importar_nfse'))

        try:
            xml_content = arquivo.read().decode('utf-8', errors='ignore')
            dados, erro = extrair_dados_nfse(xml_content)
            if erro or not dados:
                flash(f'Erro ao ler XML: {erro or "dados não extraídos"}', 'danger')
                return redirect(url_for('importacoes.importar_nfse'))

            valido, erro_validacao = validar_dados_nfse(dados)
            if not valido:
                flash(erro_validacao, 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            entidade = Entidade.query.filter_by(
                empresa_id=empresa_id,
                cnpj_cpf=dados.get('cnpj_tomador')
            ).first()

            nfse_espelho = {
                'numero_nota': dados.get('numero_nota') or '',
                'data_emissao': dados.get('data_emissao') or '',
                'cnpj_tomador': dados.get('cnpj_tomador') or '',
                'valor_bruto': dados.get('valor_bruto', 0.0),
                'descricao_servico': dados.get('descricao_servico') or '',
                'chave_nota': dados.get('chave_nota') or '',
                'aliquota_iss': dados.get('aliquota_iss', 0.0),
                'valor_iss': dados.get('valor_iss', 0.0),
                'origem_aliquota': dados.get('debug_aliquota_iss_origem') or '',
                'entidade_nome': entidade.nome if entidade else 'Não identificado',
                'entidade_tipo': entidade.get_tipo_descricao() if entidade else 'Não identificado',
            }
            return render_template('importacoes/espelho_nfse.html', nfse=nfse_espelho)
        except Exception as exc:
            logger.error('Erro ao preparar espelho NFSe: %s', exc)
            flash(f'Erro ao preparar espelho da NFSe: {exc}', 'danger')
            return redirect(url_for('importacoes.importar_nfse'))

    return render_template('importacoes/importar_nfse.html')


@importacoes_bp.route('/ofx', methods=['GET', 'POST'])
@login_required
def importar_ofx():
    """Importar extratos bancários em formato OFX"""
    
    if request.method == 'GET':
        # Mostrar formulário de upload
        contas = ContaBanco.query.filter_by(empresa_id=current_user.empresa_id).all()
        return render_template('importacoes/importar_ofx.html', contas=contas)
    
    # POST: processar upload
    if 'file' not in request.files:
        flash('Nenhum arquivo foi enviado', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))
    
    file = request.files['file']
    conta_banco_id = request.form.get('conta_banco_id')
    modo_importacao = request.form.get('modo_importacao', 'conciliar').strip().lower()
    
    if not file or file.filename == '':
        flash('Arquivo inválido', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))
    
    if not conta_banco_id:
        flash('Selecione uma conta bancária', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))

    if modo_importacao not in ('conciliar', 'lancamentos_diretos'):
        flash('Modo de importação inválido', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))
    
    # Validar que a conta pertence à empresa do usuário
    conta = ContaBanco.query.filter_by(
        id=conta_banco_id,
        empresa_id=current_user.empresa_id
    ).first()
    
    if not conta:
        flash('Conta bancária não encontrada ou acesso negado', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))
    
    try:
        content = file.read().decode('utf-8', errors='ignore')

        if modo_importacao == 'conciliar':
            conciliacao = criar_conciliacao_ofx(
                empresa_id=current_user.empresa_id,
                conta_banco_id=conta.id,
                ofx_content=content,
                criado_por_user_id=current_user.id,
            )
            resultado = reconciliar_conciliacao(conciliacao.id, current_user.empresa_id)

            flash(
                (
                    f'OFX importado para conciliação: '
                    f'{resultado["conciliados"]} conciliados, '
                    f'{resultado["pendentes"]} pendentes, '
                    f'{resultado["divergentes"]} divergentes. '
                    f'Nenhum lançamento novo foi criado automaticamente.'
                ),
                'success' if resultado['conciliados'] else 'warning'
            )
            return redirect(url_for('conciliacao.detalhe', conciliacao_id=conciliacao.id))

        resumo = _importar_ofx_com_lancamentos_diretos(
            empresa_id=current_user.empresa_id,
            conta_banco_id=conta.id,
            ofx_content=content,
        )
        flash(
            (
                f'OFX importado com lançamentos diretos: '
                f'{resumo["importados"]} criados, '
                f'{resumo["ignorados"]} ignorados (já existentes ou inválidos), '
                f'{resumo["total"]} transações no arquivo.'
            ),
            'success' if resumo['importados'] else 'warning'
        )
        return redirect(url_for('lancamentos.index', conta_banco_id=conta.id))

    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao importar OFX: {str(e)}')
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        return redirect(url_for('importacoes.importar_ofx'))
