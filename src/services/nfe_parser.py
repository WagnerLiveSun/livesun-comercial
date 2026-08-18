"""Parser de XML de NF-e para importação de compras."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional


def parse_nfe_xml(xml_content: str) -> Dict:
    """
    Extrai dados de um XML de NF-e e retorna estrutura JSON.
    
    Args:
        xml_content: Conteúdo do XML como string
        
    Returns:
        Dicionário com dados parseados da NF-e
    """
    try:
        root = ET.fromstring(xml_content)
        
        # Namespace padrão da NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Extrair dados do cabeçalho (ide)
        ide = root.find('.//nfe:ide', ns)
        dados_cabecalho = {
            'nNF': ide.findtext('nfe:nNF', namespaces=ns),
            'serie': ide.findtext('nfe:serie', namespaces=ns),
            'dhEmi': ide.findtext('nfe:dhEmi', namespaces=ns),
            'natOp': ide.findtext('nfe:natOp', namespaces=ns),
            'mod': ide.findtext('nfe:mod', namespaces=ns),
            'tpNF': ide.findtext('nfe:tpNF', namespaces=ns),
        }
        
        # Converter data de emissão
        if dados_cabecalho['dhEmi']:
            try:
                dt = datetime.fromisoformat(dados_cabecalho['dhEmi'].replace('Z', '+00:00'))
                dados_cabecalho['data_emissao'] = dt.date().isoformat()
            except:
                dados_cabecalho['data_emissao'] = None
        
        # Extrair dados do emitente
        emit = root.find('.//nfe:emit', ns)
        dados_emitente = {
            'CNPJ': emit.findtext('nfe:CNPJ', namespaces=ns),
            'xNome': emit.findtext('nfe:xNome', namespaces=ns),
            'xFant': emit.findtext('nfe:xFant', namespaces=ns),
            'IE': emit.findtext('nfe:IE', namespaces=ns),
        }
        
        # Extrair endereço do emitente
        enderEmit = emit.find('nfe:enderEmit', ns)
        if enderEmit is not None:
            dados_emitente['endereco'] = {
                'xLgr': enderEmit.findtext('nfe:xLgr', namespaces=ns),
                'nro': enderEmit.findtext('nfe:nro', namespaces=ns),
                'xCpl': enderEmit.findtext('nfe:xCpl', namespaces=ns),
                'xBairro': enderEmit.findtext('nfe:xBairro', namespaces=ns),
                'cMun': enderEmit.findtext('nfe:cMun', namespaces=ns),
                'xMun': enderEmit.findtext('nfe:xMun', namespaces=ns),
                'UF': enderEmit.findtext('nfe:UF', namespaces=ns),
                'CEP': enderEmit.findtext('nfe:CEP', namespaces=ns),
                'fone': enderEmit.findtext('nfe:fone', namespaces=ns),
            }
        
        # Extrair dados do destinatário (para referência)
        dest = root.find('.//nfe:dest', ns)
        dados_destinatario = {
            'CNPJ': dest.findtext('nfe:CNPJ', namespaces=ns),
            'xNome': dest.findtext('nfe:xNome', namespaces=ns),
        }
        
        # Extrair itens
        itens = []
        for det in root.findall('.//nfe:det', ns):
            prod = det.find('nfe:prod', ns)
            item = {
                'nItem': det.get('nItem'),
                'cProd': prod.findtext('nfe:cProd', namespaces=ns),
                'cEAN': prod.findtext('nfe:cEAN', namespaces=ns),
                'xProd': prod.findtext('nfe:xProd', namespaces=ns),
                'NCM': prod.findtext('nfe:NCM', namespaces=ns),
                'CFOP': prod.findtext('nfe:CFOP', namespaces=ns),
                'uCom': prod.findtext('nfe:uCom', namespaces=ns),
                'qCom': prod.findtext('nfe:qCom', namespaces=ns),
                'vUnCom': prod.findtext('nfe:vUnCom', namespaces=ns),
                'vProd': prod.findtext('nfe:vProd', namespaces=ns),
                'cEANTrib': prod.findtext('nfe:cEANTrib', namespaces=ns),
                'uTrib': prod.findtext('nfe:uTrib', namespaces=ns),
                'qTrib': prod.findtext('nfe:qTrib', namespaces=ns),
                'vUnTrib': prod.findtext('nfe:vUnTrib', namespaces=ns),
            }
            
            # Converter valores numéricos
            if item['qCom']:
                item['qCom'] = float(item['qCom'])
            if item['vUnCom']:
                item['vUnCom'] = float(item['vUnCom'])
            if item['vProd']:
                item['vProd'] = float(item['vProd'])
            if item['qTrib']:
                item['qTrib'] = float(item['qTrib'])
            if item['vUnTrib']:
                item['vUnTrib'] = float(item['vUnTrib'])
            
            itens.append(item)
        
        # Extrair totais
        total = root.find('.//nfe:total/nfe:ICMSTot', ns)
        dados_totais = {
            'vBC': total.findtext('nfe:vBC', namespaces=ns),
            'vICMS': total.findtext('nfe:vICMS', namespaces=ns),
            'vProd': total.findtext('nfe:vProd', namespaces=ns),
            'vNF': total.findtext('nfe:vNF', namespaces=ns),
        }
        
        # Converter valores numéricos
        if dados_totais['vProd']:
            dados_totais['vProd'] = float(dados_totais['vProd'])
        if dados_totais['vNF']:
            dados_totais['vNF'] = float(dados_totais['vNF'])
        
        return {
            'cabecalho': dados_cabecalho,
            'emitente': dados_emitente,
            'destinatario': dados_destinatario,
            'itens': itens,
            'totais': dados_totais,
        }
        
    except Exception as e:
        raise ValueError(f'Erro ao parsear XML de NF-e: {str(e)}')


def formatar_cnpj(cnpj: str) -> str:
    """Remove caracteres não numéricos do CNPJ."""
    if not cnpj:
        return ''
    return ''.join(filter(str.isdigit, cnpj))


def formatar_cep(cep: str) -> str:
    """Remove caracteres não numéricos do CEP."""
    if not cep:
        return ''
    return ''.join(filter(str.isdigit, cep))


def formatar_telefone(telefone: str) -> str:
    """Remove caracteres não numéricos do telefone."""
    if not telefone:
        return ''
    return ''.join(filter(str.isdigit, telefone))
