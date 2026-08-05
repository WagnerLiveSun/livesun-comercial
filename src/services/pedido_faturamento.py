"""Serviços para faturamento de pedidos com separação fiscal (NF-e/NFS-e)."""

from decimal import Decimal
from datetime import date
from typing import tuple, list, dict

from src.models import (
    PedidoVenda,
    PedidoVendaItem,
    Entidade,
    Produto,
    Servico,
    Empresa,
    NfseNacionalConfiguracao,
    NfseMunicipioReferencia,
    NfseServicoNacionalReferencia,
    NfseNbsReferencia,
    db,
)


def separar_itens_por_natureza(pedido: PedidoVenda) -> dict:
    """
    Separa itens do pedido por natureza fiscal.
    
    Returns:
        dict: {'produtos': list[PedidoVendaItem], 'servicos': list[PedidoVendaItem]}
    """
    produtos = [item for item in pedido.itens if item.tipo_item == 'P']
    servicos = [item for item in pedido.itens if item.tipo_item == 'S']
    
    return {
        'produtos': produtos,
        'servicos': servicos,
        'valor_produtos': sum(item.valor_total for item in produtos),
        'valor_servicos': sum(item.valor_total for item in servicos),
    }


def validar_cliente_documento_venda(cliente: Entidade) -> tuple[bool, list[str]]:
    """
    Valida se cliente possui dados completos para documento não fiscal.
    
    Returns:
        tuple: (valido, lista_erros)
    """
    erros = []
    
    campos_obrigatorios = [
        ('tipo', 'Tipo'),
        ('cnpj_cpf', 'CNPJ/CPF'),
        ('nome', 'Nome/Razão Social'),
        ('endereco_rua', 'Rua'),
        ('endereco_numero', 'Número'),
        ('endereco_bairro', 'Bairro'),
        ('endereco_cidade', 'Cidade'),
        ('endereco_uf', 'UF'),
        ('endereco_cep', 'CEP'),
        ('email', 'E-mail'),
    ]
    
    for campo, label in campos_obrigatorios:
        valor = getattr(cliente, campo, None)
        if valor is None or str(valor).strip() == '':
            erros.append(f"{label}")
    
    # Validar CNPJ/CPF
    documento = cliente.cnpj_cpf or ""
    documento_numerico = ''.join(ch for ch in str(documento) if ch.isdigit())
    if len(documento_numerico) not in [11, 14]:
        erros.append("CNPJ/CPF deve ter 11 ou 14 dígitos")
    
    return (len(erros) == 0, erros)


def validar_cliente_nfse(cliente: Entidade) -> tuple[bool, list[str]]:
    """
    Valida se cliente (tomador) possui dados completos para NFS-e.
    
    Returns:
        tuple: (valido, lista_erros)
    """
    erros = []
    
    # Validar campos básicos
    campos_obrigatorios = [
        ('tipo', 'Tipo'),
        ('cnpj_cpf', 'CNPJ/CPF'),
        ('nome', 'Nome/Razão Social'),
        ('endereco_rua', 'Rua'),
        ('endereco_numero', 'Número'),
        ('endereco_bairro', 'Bairro'),
        ('endereco_cidade', 'Cidade'),
        ('endereco_uf', 'UF'),
        ('endereco_cep', 'CEP'),
        ('email', 'E-mail'),
    ]
    
    for campo, label in campos_obrigatorios:
        valor = getattr(cliente, campo, None)
        if valor is None or str(valor).strip() == '':
            erros.append(f"{label}")
    
    # Validar CNPJ/CPF
    documento = cliente.cnpj_cpf or ""
    documento_numerico = ''.join(ch for ch in str(documento) if ch.isdigit())
    if len(documento_numerico) not in [11, 14]:
        erros.append("CNPJ/CPF deve ter 11 ou 14 dígitos")
    
    # Validar código IBGE do município
    if not getattr(cliente, 'codigo_municipio_ibge', None):
        erros.append("Código IBGE do município")
    
    return (len(erros) == 0, erros)


def validar_servico_nfse(servico: Servico) -> tuple[bool, list[str]]:
    """
    Valida se serviço possui dados fiscais completos para NFS-e.
    
    Returns:
        tuple: (valido, lista_erros)
    """
    erros = []
    
    campos_obrigatorios = [
        ('codigo_interno', 'Código interno'),
        ('descricao', 'Descrição'),
        ('codigo_servico', 'Código de serviço nacional'),
        ('nbs', 'NBS'),
    ]
    
    for campo, label in campos_obrigatorios:
        valor = getattr(servico, campo, None)
        if valor is None or str(valor).strip() == '':
            erros.append(f"{label}")
    
    # Validar código de serviço nacional na tabela oficial
    if servico.codigo_servico:
        servico_nacional = NfseServicoNacionalReferencia.query.filter_by(
            codigo_tributacao_nacional=servico.codigo_servico,
            ativo=True
        ).first()
        if not servico_nacional:
            erros.append(f"Código de serviço nacional {servico.codigo_servico} não encontrado na tabela oficial")
    
    # Validar NBS na tabela oficial
    if servico.nbs:
        nbs_valido = NfseNbsReferencia.query.filter_by(
            codigo_nbs=servico.nbs,
            ativo=True
        ).first()
        if not nbs_valido:
            erros.append(f"NBS {servico.nbs} não encontrado na tabela oficial")
    
    return (len(erros) == 0, erros)


def validar_produto(produto: Produto) -> tuple[bool, list[str]]:
    """
    Valida se produto possui dados básicos para documento não fiscal.
    
    Returns:
        tuple: (valido, lista_erros)
    """
    erros = []
    
    campos_obrigatorios = [
        ('codigo_interno', 'Código interno'),
        ('descricao_resumida', 'Descrição'),
    ]
    
    for campo, label in campos_obrigatorios:
        valor = getattr(produto, campo, None)
        if valor is None or str(valor).strip() == '':
            erros.append(f"{label}")
    
    return (len(erros) == 0, erros)


def validar_empresa_nfse(empresa: Empresa) -> tuple[bool, list[str]]:
    """
    Valida se empresa possui configurações NFS-e válidas.
    
    Returns:
        tuple: (valido, lista_erros)
    """
    erros = []
    
    # Validar código IBGE do município
    if not getattr(empresa, 'codigo_municipio_ibge', None):
        erros.append("Código IBGE do município")
    
    # Validar configuração NFS-e
    configuracao = NfseNacionalConfiguracao.query.filter_by(
        empresa_id=empresa.id,
        emissor_ativo=True
    ).first()
    
    if not configuracao:
        erros.append("Configuração NFS-e ativa")
    else:
        # Validar certificado
        from src.routes.nfse_nacional import _inspect_certificate
        from src.models import NfseNacionalCertificado
        
        certificado = NfseNacionalCertificado.query.filter_by(
            empresa_id=empresa.id,
            ambiente=configuracao.ambiente,
            ativo=True
        ).first()
        
        if not certificado:
            erros.append("Certificado digital configurado")
        else:
            validade, status = _inspect_certificate(certificado)
            if not validade:
                erros.append(f"Certificado digital: {status}")
    
    return (len(erros) == 0, erros)


def validar_faturamento_pedido(pedido: PedidoVenda) -> tuple[bool, dict]:
    """
    Valida se pedido pode ser faturado com separação fiscal.
    
    Returns:
        tuple: (valido, dict_com_erros)
        dict_com_erros: {
            'cliente_documento_venda': list[str],
            'cliente_nfse': list[str],
            'servicos': {servico_id: list[str]},
            'produtos': {produto_id: list[str]},
            'empresa_nfse': list[str],
        }
    """
    erros = {
        'cliente_documento_venda': [],
        'cliente_nfse': [],
        'servicos': {},
        'produtos': {},
        'empresa_nfse': [],
    }
    
    # Separar itens
    itens_por_natureza = separar_itens_por_natureza(pedido)
    
    # Validar cliente para documento não fiscal (se houver produtos)
    if itens_por_natureza['produtos']:
        valido, erros_lista = validar_cliente_documento_venda(pedido.cliente)
        if not valido:
            erros['cliente_documento_venda'] = erros_lista
    
    # Validar cliente para NFS-e (se houver serviços)
    if itens_por_natureza['servicos']:
        valido, erros_lista = validar_cliente_nfse(pedido.cliente)
        if not valido:
            erros['cliente_nfse'] = erros_lista
    
    # Validar serviços
    for item in itens_por_natureza['servicos']:
        if item.servico:
            valido, erros_lista = validar_servico_nfse(item.servico)
            if not valido:
                erros['servicos'][item.servico_id] = erros_lista
    
    # Validar produtos
    for item in itens_por_natureza['produtos']:
        if item.produto:
            valido, erros_lista = validar_produto(item.produto)
            if not valido:
                erros['produtos'][item.produto_id] = erros_lista
    
    # Validar empresa para NFS-e (se houver serviços)
    if itens_por_natureza['servicos']:
        valido, erros_lista = validar_empresa_nfse(pedido.empresa)
        if not valido:
            erros['empresa_nfse'] = erros_lista
    
    # Verificar se há algum erro
    tem_erros = any(
        len(erros_lista) > 0 
        for erros_lista in erros.values() 
        if isinstance(erros_lista, list)
    ) or any(
        len(erros_item) > 0 
        for erros_item in erros['servicos'].values()
    ) or any(
        len(erros_item) > 0 
        for erros_item in erros['produtos'].values()
    )
    
    return (not tem_erros, erros)


def formatar_erros_validacao(erros: dict) -> list[str]:
    """
    Formata erros de validação em lista de mensagens.
    
    Returns:
        list[str]: Lista de mensagens de erro formatadas
    """
    mensagens = []
    
    if erros['cliente_documento_venda']:
        mensagens.append(f"Cliente (documento não fiscal): {', '.join(erros['cliente_documento_venda'])}")
    
    if erros['cliente_nfse']:
        mensagens.append(f"Cliente (NFS-e): {', '.join(erros['cliente_nfse'])}")
    
    if erros['empresa_nfse']:
        mensagens.append(f"Empresa (NFS-e): {', '.join(erros['empresa_nfse'])}")
    
    for servico_id, erros_lista in erros['servicos'].items():
        mensagens.append(f"Serviço ID {servico_id}: {', '.join(erros_lista)}")
    
    for produto_id, erros_lista in erros['produtos'].items():
        mensagens.append(f"Produto ID {produto_id}: {', '.join(erros_lista)}")
    
    return mensagens
