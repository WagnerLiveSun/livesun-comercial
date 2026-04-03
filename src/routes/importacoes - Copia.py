"""
Rotas para importação de NFSe (Notas de Serviço)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime


import zipfile
try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False
import xml.etree.ElementTree as ET
from src.models import db, ImportacaoNFSe

importacoes_bp = Blueprint('importacoes - importacoes.py:21', __name__, url_prefix='/importacoes')

ALLOWED_EXTENSIONS = {'xml', 'zip', 'rar'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def processar_xml_nfse(xml_content, empresa_id):
    try:
        tree = ET.ElementTree(ET.fromstring(xml_content))
        root = tree.getroot()
        ns = {'n': root.tag.split('}')[0].strip('{')}  # namespace principal

        # Busca campos conforme padrão nacional NFS-e
        inf_nfse = root.find('.//n:infNFSe', ns)
        if inf_nfse is None:
            return False, 'XML não possui tag infNFSe (padrão nacional).'

        numero_nota = inf_nfse.findtext('n:nNFSe', default='', namespaces=ns)
        data_emissao = inf_nfse.findtext('n:dhProc', default='', namespaces=ns)
        cnpj_tomador = inf_nfse.findtext('n:DPS/n:infDPS/n:toma/n:CNPJ', default='', namespaces=ns)
        valor_bruto_str = inf_nfse.findtext('n:valores/n:vLiq', default='', namespaces=ns)
        descricao_servico = inf_nfse.findtext('n:xTribNac', default='', namespaces=ns)
        chave_nota = inf_nfse.get('Id') or numero_nota

        # Validação de campos obrigatórios
        campos_faltando = []
        if not numero_nota:
            campos_faltando.append('Número da Nota')
        if not data_emissao:
            campos_faltando.append('Data de Emissão')
        if not cnpj_tomador:
            campos_faltando.append('CNPJ do Tomador')
        if not valor_bruto_str:
            campos_faltando.append('Valor Líquido')
        # Tenta converter valor_bruto
        try:
            valor_bruto = float(valor_bruto_str.replace(',', '.')) if valor_bruto_str else 0
        except Exception:
            campos_faltando.append('Valor Líquido (inválido)')
            valor_bruto = 0
        if campos_faltando:
            return False, f'Campos obrigatórios ausentes ou inválidos no XML: {", ".join(campos_faltando)}.'

        # Normaliza campos
        if not chave_nota:
            chave_nota = f"{numero_nota}-{cnpj_tomador}"
        # Deduplicação
        existe = ImportacaoNFSe.query.filter_by(empresa_id=empresa_id, chave_nota=chave_nota).first()
        if existe:
            return False, f'Nota já importada: {chave_nota}'
        # Busca ou cria entidade do tomador
        from src.models import Entidade
        entidade = Entidade.query.filter_by(empresa_id=empresa_id, cnpj_cpf=cnpj_tomador).first()
        fluxo_conta_id = None
        if not entidade:
            try:
                from src.models import FluxoContaModel
                fluxo_conta = FluxoContaModel.query.filter_by(empresa_id=empresa_id, codigo='1.1.1').first()
                fluxo_conta_id = fluxo_conta.id if fluxo_conta else None
                entidade = Entidade(
                    empresa_id=empresa_id,
                    tipo='C',  # Cliente por padrão
                    nome=f'Tomador {cnpj_tomador}',
                    cnpj_cpf=cnpj_tomador,
                    ativo=True,
                    fluxo_conta_id=fluxo_conta_id
                )
                db.session.add(entidade)
                db.session.flush()  # Garante que entidade.id está disponível
            except Exception as e:
                db.session.rollback()
                return False, f'Erro ao criar Entidade: {str(e)} | empresa_id={empresa_id} cnpj_cpf={cnpj_tomador}'
        else:
            fluxo_conta_id = entidade.fluxo_conta_id

        # Buscar conta bancária principal da empresa
        from src.models import ContaBanco, Lancamento
        conta_principal = ContaBanco.query.filter_by(empresa_id=empresa_id, is_principal=True).first()
        conta_banco_id = conta_principal.id if conta_principal else None

        # Criar lançamento financeiro
        try:
            data_emissao_dt = None
            if data_emissao:
                try:
                    data_emissao_dt = datetime.strptime(data_emissao[:10], '%Y-%m-%d').date()
                except Exception:
                    data_emissao_dt = datetime.utcnow().date()
            lancamento = Lancamento(
                empresa_id=empresa_id,
                entidade_id=entidade.id,
                fluxo_conta_id=fluxo_conta_id,
                conta_banco_id=conta_banco_id,
                data_evento=data_emissao_dt,
                data_vencimento=data_emissao_dt,
                status='aberto',
                valor_real=valor_bruto,
                valor_pago=0.00,
                valor_imposto=0.00,
                valor_outros_custos=0.00,
                numero_documento=numero_nota or chave_nota,
                observacoes=descricao_servico or ''
            )
            db.session.add(lancamento)
        except Exception as e:
            db.session.rollback()
            return False, f'Erro ao criar Lançamento: {str(e)}'
        # Cria registro
        registro = ImportacaoNFSe(
            empresa_id=empresa_id,
            chave_nota=chave_nota,
            numero_nota=numero_nota or '',
            data_emissao=data_emissao[:10] if data_emissao else None,
            cnpj_tomador=cnpj_tomador or '',
            valor_bruto=valor_bruto,
            valor_impostos=None,
            descricao_servico=descricao_servico or '',
            entidade_id=entidade.id
        )
        db.session.add(registro)
        db.session.commit()
        return True, f'Nota importada: {chave_nota}'
    except Exception as e:
        db.session.rollback()
        return False, f'Erro ao importar XML: {str(e)}'

def processar_arquivo_nfse(file_path, empresa_id, mensagens):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xml':
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        ok, msg = processar_xml_nfse(xml_content, empresa_id)
        mensagens.append(msg)
    elif ext == '.zip':
        with zipfile.ZipFile(file_path, 'r') as z:
            for name in z.namelist():
                if name.lower().endswith('.xml'):
                    with z.open(name) as f:
                        xml_content = f.read().decode('utf-8')
                    ok, msg = processar_xml_nfse(xml_content, empresa_id)
                    mensagens.append(f'{name}: {msg}')
    elif ext == '.rar' and HAS_RAR:
        with rarfile.RarFile(file_path, 'r') as r:
            for name in r.namelist():
                if name.lower().endswith('.xml'):
                    with r.open(name) as f:
                        xml_content = f.read().decode('utf-8')
                    ok, msg = processar_xml_nfse(xml_content, empresa_id)
                    mensagens.append(f'{name}: {msg}')
    else:
        mensagens.append('Tipo de arquivo não suportado para processamento.')

@importacoes_bp.route('/nfse', methods=['GET', 'POST'])
@login_required
def importar_nfse():
    if request.method == 'POST':
        # Confirmação do espelho (agora usa dados do formulário, não mais xml_content)
        if 'confirmar' in request.form:
            numero_nota = request.form.get('numero_nota')
            data_emissao = request.form.get('data_emissao')
            cnpj_tomador = request.form.get('cnpj_tomador')
            valor_bruto = request.form.get('valor_bruto')
            descricao_servico = request.form.get('descricao_servico')
            chave_nota = request.form.get('chave_nota')

            from src.models import Entidade, FluxoContaModel, ContaBanco, Lancamento, ImportacaoNFSe, db
            empresa_id = current_user.empresa_id
            erros = []

            # Impedir duplicidade de chave_nota
            duplicado = ImportacaoNFSe.query.filter_by(empresa_id=empresa_id, chave_nota=chave_nota).first()
            if duplicado:
                flash(f'Nota já importada: {chave_nota}', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Buscar entidade existente
            entidade = Entidade.query.filter_by(empresa_id=empresa_id, cnpj_cpf=cnpj_tomador).first()
            if not entidade:
                erros.append('Entidade (cliente) não encontrada para o CNPJ informado. Cadastre a entidade antes de importar.')
            if entidade and not entidade.tipo:
                erros.append('Entidade encontrada, mas sem tipo definido (C/V/F).')

            # Buscar fluxo de caixa da entidade
            fluxo_conta_id = entidade.fluxo_conta_id if entidade else None
            if not fluxo_conta_id:
                erros.append('Entidade não possui conta de fluxo de caixa associada.')

            # Buscar conta bancária principal da empresa
            conta_principal = ContaBanco.query.filter_by(empresa_id=empresa_id, is_principal=True).first()
            conta_banco_id = conta_principal.id if conta_principal else None
            if not conta_banco_id:
                erros.append('Empresa não possui conta bancária principal cadastrada.')

            if erros:
                for erro in erros:
                    flash(erro, 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Criar lançamento financeiro
            try:
                data_emissao_dt = None
                if data_emissao:
                    try:
                        data_emissao_dt = datetime.strptime(data_emissao[:10], '%Y-%m-%d').date()
                    except Exception:
                        data_emissao_dt = datetime.utcnow().date()
                lancamento = Lancamento(
                    empresa_id=empresa_id,
                    entidade_id=entidade.id,
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco_id,
                    data_evento=data_emissao_dt,
                    data_vencimento=data_emissao_dt,
                    status='aberto',
                    valor_real=valor_bruto,
                    valor_pago=0.00,
                    valor_imposto=0.00,
                    valor_outros_custos=0.00,
                    numero_documento=numero_nota or chave_nota,
                    observacoes=descricao_servico or ''
                )
                db.session.add(lancamento)
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar Lançamento: {str(e)}', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Cria registro de importação
            try:
                registro = ImportacaoNFSe(
                    empresa_id=empresa_id,
                    chave_nota=chave_nota,
                    numero_nota=numero_nota or '',
                    data_emissao=data_emissao[:10] if data_emissao else None,
                    cnpj_tomador=cnpj_tomador or '',
                    valor_bruto=valor_bruto,
                    valor_impostos=None,
                    descricao_servico=descricao_servico or '',
                    entidade_id=entidade.id
                )
                db.session.add(registro)
                db.session.commit()
                flash(f'Nota importada: {chave_nota}', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao registrar importação: {str(e)}', 'warning')
            return redirect(url_for('importacoes.importar_nfse'))
    return render_template('importacoes/importar_nfse.html')

            # Criar lançamento financeiro
            try:
                data_emissao_dt = None
                if data_emissao:
                    try:
                        data_emissao_dt = datetime.strptime(data_emissao[:10], '%Y-%m-%d').date()
                    except Exception:
                        data_emissao_dt = datetime.utcnow().date()
                lancamento = Lancamento(
                    empresa_id=empresa_id,
                    entidade_id=entidade.id,
                    fluxo_conta_id=fluxo_conta_id,
                    conta_banco_id=conta_banco_id,
                    data_evento=data_emissao_dt,
                    data_vencimento=data_emissao_dt,
                    status='aberto',
                    valor_real=valor_bruto,
                    valor_pago=0.00,
                    valor_imposto=0.00,
                    valor_outros_custos=0.00,
                    numero_documento=numero_nota or chave_nota,
                    observacoes=descricao_servico or ''
                )
                db.session.add(lancamento)
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar Lançamento: {str(e)}', 'warning')
                return redirect(url_for('importacoes.importar_nfse'))

            # Cria registro de importação
            try:
                registro = ImportacaoNFSe(
                    empresa_id=empresa_id,
                    chave_nota=chave_nota,
                    numero_nota=numero_nota or '',
                    data_emissao=data_emissao[:10] if data_emissao else None,
                    cnpj_tomador=cnpj_tomador or '',
                    valor_bruto=valor_bruto,
                    valor_impostos=None,
                    descricao_servico=descricao_servico or '',
                    entidade_id=entidade.id
                )
                db.session.add(registro)
                db.session.commit()
                flash(f'Nota importada: {chave_nota}', 'info')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao registrar importação: {str(e)}', 'warning')
            return redirect(url_for('importacoes.importar_nfse'))

        # Upload de arquivo
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado no formulário.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado para upload.', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            ext = os.path.splitext(filename)[1].lower()
            # Se for XML individual, mostrar espelho antes de importar
            if ext == '.xml':
                with open(file_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                # Extrai dados para o espelho
                tree = ET.ElementTree(ET.fromstring(xml_content))
                root = tree.getroot()
                ns = {'n': root.tag.split('}')[0].strip('{')}
                inf_nfse = root.find('.//n:infNFSe', ns)
                if inf_nfse is not None:
                    numero_nota = inf_nfse.findtext('n:nNFSe', default='', namespaces=ns)
                    data_emissao = inf_nfse.findtext('n:dhProc', default='', namespaces=ns)
                    cnpj_tomador = inf_nfse.findtext('n:DPS/n:infDPS/n:toma/n:CNPJ', default='', namespaces=ns)
                    valor_bruto = inf_nfse.findtext('n:valores/n:vLiq', default='', namespaces=ns)
                    descricao_servico = inf_nfse.findtext('n:xTribNac', default='', namespaces=ns)
                    chave_nota = inf_nfse.get('Id') or numero_nota
                    nfse = {
                        'numero_nota': numero_nota,
                        'data_emissao': data_emissao,
                        'cnpj_tomador': cnpj_tomador,
                        'valor_bruto': valor_bruto,
                        'descricao_servico': descricao_servico,
                        'chave_nota': chave_nota
                    }
                    return render_template('importacoes/espelho_nfse.html', nfse=nfse, xml_content=xml_content)
                else:
                    flash('XML não possui tag infNFSe (padrão nacional).', 'warning')
                    return redirect(request.url)
            else:
                # Lote/compactado: importa direto
                mensagens = []
                processar_arquivo_nfse(file_path, current_user.empresa_id, mensagens)
                for msg in mensagens:
                    flash(msg, 'info' if 'importada' in msg else 'warning')
                return redirect(url_for('importacoes.importar_nfse'))
        else:
            flash('Tipo de arquivo não suportado.', 'danger')
            return redirect(request.url)
    return render_template('importacoes/importar_nfse.html')
