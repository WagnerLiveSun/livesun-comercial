# Serviços e APIs - Módulo de Gestão de Contratos

## Arquitetura de Serviços

O módulo de contratos segue uma arquitetura em camadas com serviços de negócio bem definidos.

## 1. Serviço de Geração de Contratos

### ContratoService

**Responsabilidade:** Gerenciar o ciclo de vida dos contratos (criação, edição, status).

#### Métodos Principais

##### gerar_contrato_from_orcamento(orcamento_id, user_id)

Gera um novo contrato a partir de um orçamento aprovado.

```python
def gerar_contrato_from_orcamento(orcamento_id: int, user_id: int) -> Contrato:
    """
    Gera um contrato a partir de um orçamento aprovado.
    
    Args:
        orcamento_id: ID do orçamento aprovado
        user_id: ID do usuário que está gerando o contrato
        
    Returns:
        Contrato: Objeto do contrato gerado
        
    Raises:
        ValueError: Se orçamento não existe ou não está aprovado
    """
    # 1. Validar orçamento
    orcamento = Orcamento.query.get_or_404(orcamento_id)
    if orcamento.status != 'aprovado':
        raise ValueError("Orçamento deve estar aprovado para gerar contrato")
    
    # 2. Verificar se já existe contrato para este orçamento
    contrato_existente = Contrato.query.filter_by(orcamento_id=orcamento_id).first()
    if contrato_existente:
        raise ValueError("Já existe contrato para este orçamento")
    
    # 3. Buscar entidades (contratada e contratante)
    empresa = Empresa.query.get(orcamento.empresa_id)
    cliente = Entidade.query.get(orcamento.cliente_id)
    contratada = buscar_entidade_contratada(empresa.id)
    
    # 4. Gerar número do contrato
    numero = gerar_numero_contrato(empresa.id)
    
    # 5. Criar contrato
    contrato = Contrato(
        empresa_id=empresa.id,
        numero=numero,
        serie='CTR',
        orcamento_id=orcamento.id,
        cliente_id=cliente.id,
        vendedor_id=orcamento.vendedor_id,
        contratada_entidade_id=contratada.id,
        contratante_entidade_id=cliente.id,
        valor_total=orcamento.valor_total,
        valor_mensal=calcular_valor_mensal(orcamento),
        forma_pagamento=orcamento.forma_pagamento,
        periodicidade=orcamento.periodicidade,
        data_inicio_vigencia=orcamento.data_inicio or date.today(),
        data_fim_vigencia=orcamento.data_fim,
        status='rascunho',
        descricao_servicos=gerar_descricao_servicos(orcamento),
        gerado_por_user_id=user_id
    )
    
    db.session.add(contrato)
    db.session.flush()
    
    # 6. Gerar cláusulas automáticas
    gerar_clausulas_automaticas(contrato, orcamento)
    
    # 7. Gerar parâmetros de substituição
    gerar_parametros_contrato(contrato, orcamento, empresa, cliente, contratada)
    
    # 8. Registrar histórico
    registrar_historico_contrato(contrato, 'criado', user_id)
    
    db.session.commit()
    
    return contrato
```

##### atualizar_contrato(contrato_id, dados, user_id)

Atualiza dados do contrato.

```python
def atualizar_contrato(contrato_id: int, dados: dict, user_id: int) -> Contrato:
    """
    Atualiza dados do contrato.
    
    Args:
        contrato_id: ID do contrato
        dados: Dicionário com campos a atualizar
        user_id: ID do usuário que está atualizando
        
    Returns:
        Contrato: Objeto do contrato atualizado
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    
    # Validar status
    if contrato.status in ['assinado', 'cancelado']:
        raise ValueError("Contrato assinado ou cancelado não pode ser editado")
    
    # Registrar campos alterados
    campos_alterados = []
    for campo, valor in dados.items():
        if hasattr(contrato, campo) and getattr(contrato, campo) != valor:
            campos_alterados.append(campo)
            setattr(contrato, campo, valor)
    
    if campos_alterados:
        contrato.atualizado_em = datetime.utcnow()
        registrar_historico_contrato(
            contrato, 
            'editado', 
            user_id, 
            campos_alterados=campos_alterados
        )
        db.session.commit()
    
    return contrato
```

##### alterar_status_contrato(contrato_id, novo_status, user_id, motivo=None)

Altera o status do contrato.

```python
def alterar_status_contrato(contrato_id: int, novo_status: str, user_id: int, motivo: str = None):
    """
    Altera o status do contrato.
    
    Args:
        contrato_id: ID do contrato
        novo_status: Novo status ('rascunho', 'aguardando_assinatura', 'assinado', 'cancelado', 'rescindido')
        user_id: ID do usuário
        motivo: Motivo da alteração (opcional)
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    status_anterior = contrato.status
    
    # Validar transição de status
    transicoes_validas = {
        'rascunho': ['aguardando_assinatura', 'cancelado'],
        'aguardando_assinatura': ['assinado', 'cancelado', 'rascunho'],
        'assinado': ['rescindido', 'cancelado'],
        'cancelado': [],
        'rescindido': []
    }
    
    if novo_status not in transicoes_validas.get(status_anterior, []):
        raise ValueError(f"Transição de status inválida: {status_anterior} → {novo_status}")
    
    contrato.status = novo_status
    
    if novo_status == 'assinado':
        contrato.data_assinatura = date.today()
        contrato.assinado_por_user_id = user_id
    elif novo_status in ['cancelado', 'rescindido']:
        contrato.motivo_cancelamento = motivo
    
    registrar_historico_contrato(
        contrato,
        novo_status,
        user_id,
        status_anterior=status_anterior,
        descricao_alteracao=motivo
    )
    
    db.session.commit()
```

## 2. Serviço de Cláusulas

### ClausulaService

**Responsabilidade:** Gerenciar biblioteca de cláusulas e instâncias em contratos.

#### Métodos Principais

##### criar_clausula_padrao(dados, user_id)

Cria uma nova cláusula padrão na biblioteca.

```python
def criar_clausula_padrao(dados: dict, user_id: int) -> ClausulaContratoPadrao:
    """
    Cria uma nova cláusula padrão.
    
    Args:
        dados: Dicionário com dados da cláusula
        user_id: ID do usuário criador
        
    Returns:
        ClausulaContratoPadrao: Objeto da cláusula criada
    """
    clausula = ClausulaContratoPadrao(
        empresa_id=dados['empresa_id'],
        codigo=dados['codigo'],
        titulo=dados['titulo'],
        texto_base=dados['texto_base'],
        descricao=dados.get('descricao'),
        tipo=dados.get('tipo', 'opcional'),
        editavel=dados.get('editavel', True),
        ordem_padrao=dados.get('ordem_padrao', 0),
        categoria=dados.get('categoria'),
        tipo_contrato=dados.get('tipo_contrato'),
        criado_por_user_id=user_id
    )
    
    db.session.add(clausula)
    db.session.commit()
    
    return clausula
```

##### buscar_clausulas_por_tipo(tipo, tipo_contrato=None)

Busca cláusulas padrão por tipo e tipo de contrato.

```python
def buscar_clausulas_por_tipo(tipo: str, tipo_contrato: str = None, empresa_id: int = None):
    """
    Busca cláusulas padrão por tipo.
    
    Args:
        tipo: Tipo da cláusula ('obrigatoria', 'opcional', 'condicional')
        tipo_contrato: Tipo de contrato (opcional)
        empresa_id: ID da empresa (opcional)
        
    Returns:
        List[ClausulaContratoPadrao]: Lista de cláusulas
    """
    query = ClausulaContratoPadrao.query.filter_by(
        tipo=tipo,
        ativo=True
    )
    
    if tipo_contrato:
        query = query.filter_by(tipo_contrato=tipo_contrato)
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    return query.order_by(ClausulaContratoPadrao.ordem_padrao).all()
```

##### gerar_clausulas_automaticas(contrato, orcamento)

Gera cláusulas automáticas para um contrato.

```python
def gerar_clausulas_automaticas(contrato: Contrato, orcamento: Orcamento):
    """
    Gera cláusulas automáticas para um contrato.
    
    Args:
        contrato: Objeto do contrato
        orcamento: Objeto do orçamento
    """
    # Buscar cláusulas obrigatórias
    clausulas_obrigatorias = buscar_clausulas_por_tipo('obrigatoria', 'prestacao_servicos', contrato.empresa_id)
    
    # Buscar cláusulas opcionais padrão
    clausulas_opcionais = buscar_clausulas_por_tipo('opcional', 'prestacao_servicos', contrato.empresa_id)
    
    ordem = 1
    
    # Adicionar cláusulas obrigatórias
    for clausula_padrao in clausulas_obrigatorias:
        contrato_clausula = ContratoClausulas(
            contrato_id=contrato.id,
            clausula_padrao_id=clausula_padrao.id,
            titulo=clausula_padrao.titulo,
            texto=clausula_padrao.texto_base,
            ordem=ordem,
            editavel=clausula_padrao.editavel,
            obrigatoria=True
        )
        db.session.add(contrato_clausula)
        ordem += 1
    
    # Adicionar cláusulas opcionais selecionadas (pode ser configurável)
    for clausula_padrao in clausulas_opcoes:
        # Lógica para decidir quais cláusulas opcionais incluir
        if deve_incluir_clausula_opcional(clausula_padrao, orcamento):
            contrato_clausula = ContratoClausulas(
                contrato_id=contrato.id,
                clausula_padrao_id=clausula_padrao.id,
                titulo=clausula_padrao.titulo,
                texto=clausula_padrao.texto_base,
                ordem=ordem,
                editavel=clausula_padrao.editavel,
                obrigatoria=False
            )
            db.session.add(contrato_clausula)
            ordem += 1
```

##### atualizar_clausula_contrato(clausula_id, texto, user_id)

Atualiza o texto de uma cláusula em um contrato.

```python
def atualizar_clausula_contrato(clausula_id: int, texto: str, user_id: int):
    """
    Atualiza o texto de uma cláusula no contrato.
    
    Args:
        clausula_id: ID da cláusula do contrato
        texto: Novo texto da cláusula
        user_id: ID do usuário que está editando
    """
    clausula = ContratoClausulas.query.get_or_404(clausula_id)
    
    # Validar se é editável
    if not clausula.editavel:
        raise ValueError("Esta cláusula não pode ser editada")
    
    # Validar status do contrato
    contrato = clausula.contrato
    if contrato.status in ['assinado', 'cancelado']:
        raise ValueError("Contrato assinado ou cancelado não pode ser editado")
    
    # Atualizar
    clausula.texto = texto
    clausula.data_alteracao = datetime.utcnow()
    clausula.alterado_por_user_id = user_id
    
    # Registrar histórico
    registrar_historico_contrato(
        contrato,
        'editado',
        user_id,
        clausulas_alteradas=[{
            'clausula_id': clausula_id,
            'titulo': clausula.titulo
        }]
    )
    
    db.session.commit()
```

##### reordenar_clausulas(contrato_id, nova_ordem, user_id)

Reordena as cláusulas de um contrato.

```python
def reordenar_clausulas(contrato_id: int, nova_ordem: list[int], user_id: int):
    """
    Reordena as cláusulas de um contrato.
    
    Args:
        contrato_id: ID do contrato
        nova_ordem: Lista de IDs das cláusulas na nova ordem
        user_id: ID do usuário
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    
    if contrato.status in ['assinado', 'cancelado']:
        raise ValueError("Contrato assinado ou cancelado não pode ser editado")
    
    for idx, clausula_id in enumerate(nova_ordem):
        clausula = ContratoClausulas.query.get_or_404(clausula_id)
        if clausula.contrato_id != contrato_id:
            continue
        clausula.ordem = idx + 1
    
    registrar_historico_contrato(contrato, 'editado', user_id)
    db.session.commit()
```

##### adicionar_clausula_biblioteca(contrato_id, clausula_padrao_id, user_id)

Adiciona uma cláusula da biblioteca ao contrato.

```python
def adicionar_clausula_biblioteca(contrato_id: int, clausula_padrao_id: int, user_id: int):
    """
    Adiciona uma cláusula da biblioteca ao contrato.
    
    Args:
        contrato_id: ID do contrato
        clausula_padrao_id: ID da cláusula padrão
        user_id: ID do usuário
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    clausula_padrao = ClausulaContratoPadrao.query.get_or_404(clausula_padrao_id)
    
    if contrato.status in ['assinado', 'cancelado']:
        raise ValueError("Contrato assinado ou cancelado não pode ser editado")
    
    # Determinar próxima ordem
    max_ordem = db.session.query(func.max(ContratoClausulas.ordem)).filter_by(
        contrato_id=contrato_id
    ).scalar() or 0
    
    contrato_clausula = ContratoClausulas(
        contrato_id=contrato.id,
        clausula_padrao_id=clausula_padrao.id,
        titulo=clausula_padrao.titulo,
        texto=clausula_padrao.texto_base,
        ordem=max_ordem + 1,
        editavel=clausula_padrao.editavel,
        obrigatoria=False
    )
    
    db.session.add(contrato_clausula)
    registrar_historico_contrato(contrato, 'editado', user_id)
    db.session.commit()
```

##### remover_clausula_contrato(clausula_id, user_id)

Remove uma cláusula opcional do contrato.

```python
def remover_clausula_contrato(clausula_id: int, user_id: int):
    """
    Remove uma cláusula opcional do contrato.
    
    Args:
        clausula_id: ID da cláusula
        user_id: ID do usuário
    """
    clausula = ContratoClausulas.query.get_or_404(clausula_id)
    
    if clausula.obrigatoria:
        raise ValueError("Cláusulas obrigatórias não podem ser removidas")
    
    contrato = clausula.contrato
    if contrato.status in ['assinado', 'cancelado']:
        raise ValueError("Contrato assinado ou cancelado não pode ser editado")
    
    db.session.delete(clausula)
    
    # Reordenar cláusulas restantes
    clausulas_restantes = ContratoClausulas.query.filter_by(
        contrato_id=contrato.id
    ).order_by(ContratoClausulas.ordem).all()
    
    for idx, c in enumerate(clausulas_restantes, 1):
        c.ordem = idx
    
    registrar_historico_contrato(contrato, 'editado', user_id)
    db.session.commit()
```

## 3. Serviço de Substituição de Variáveis

### PlaceholderService

**Responsabilidade:** Gerenciar substituição de placeholders no texto das cláusulas.

#### Métodos Principais

##### substituir_placeholders(texto, contrato)

Substitui placeholders no texto pelos valores do contrato.

```python
def substituir_placeholders(texto: str, contrato: Contrato) -> str:
    """
    Substitui placeholders no texto pelos valores do contrato.
    
    Args:
        texto: Texto com placeholders
        contrato: Objeto do contrato
        
    Returns:
        str: Texto com placeholders substituídos
    """
    # Buscar valores dos parâmetros
    valores = buscar_valores_parametros(contrato.id)
    
    # Substituir cada placeholder
    for codigo, valor in valores.items():
        placeholder = f"{{{codigo}}}"
        texto = texto.replace(placeholder, str(valor))
    
    return texto
```

##### gerar_parametros_contrato(contrato, orcamento, empresa, cliente, contratada)

Gera os parâmetros de substituição para um contrato.

```python
def gerar_parametros_contrato(contrato: Contrato, orcamento: Orcamento, 
                               empresa: Empresa, cliente: Entidade, 
                               contratada: Entidade):
    """
    Gera os parâmetros de substituição para um contrato.
    
    Args:
        contrato: Objeto do contrato
        orcamento: Objeto do orçamento
        empresa: Objeto da empresa
        cliente: Objeto do cliente
        contratada: Objeto da entidade contratada
    """
    parametros = {
        # Dados da contratada
        'CONTRATADA_RAZAO_SOCIAL': contratada.nome,
        'CONTRATADA_CNPJ': formatar_cnpj(contratada.cnpj_cpf),
        'CONTRATADA_ENDERECO': formatar_endereco(contratada),
        'CONTRATADA_CIDADE': contratada.endereco_cidade,
        'CONTRATADA_UF': contratada.endereco_uf,
        
        # Dados do contratante
        'CONTRATANTE_RAZAO_SOCIAL': cliente.nome,
        'CONTRATANTE_CNPJ_CPF': formatar_cnpj_cpf(cliente.cnpj_cpf),
        'CONTRATANTE_ENDERECO': formatar_endereco(cliente),
        'CONTRATANTE_CIDADE': cliente.endereco_cidade,
        'CONTRATANTE_UF': cliente.endereco_uf,
        
        # Dados do contrato
        'CONTRATO_VALOR_TOTAL': formatar_moeda(contrato.valor_total),
        'CONTRATO_VALOR_MENSAL': formatar_moeda(contrato.valor_mensal) if contrato.valor_mensal else '',
        'CONTRATO_FORMA_PAGAMENTO': contrato.forma_pagamento,
        'CONTRATO_PERIODICIDADE': contrato.periodicidade,
        'CONTRATO_DATA_INICIO': formatar_data(contrato.data_inicio_vigencia),
        'CONTRATO_DATA_FIM': formatar_data(contrato.data_fim_vigencia) if contrato.data_fim_vigencia else '',
        'CONTRATO_DESCRICAO_SERVICOS': contrato.descricao_servicos,
        'CONTRATO_NUMERO': f"{contrato.serie}-{contrato.numero}",
        'CONTRATO_DATA_ASSINATURA': formatar_data(contrato.data_assinatura) if contrato.data_assinatura else '',
    }
    
    # Salvar no banco
    for codigo, valor in parametros.items():
        parametro = ContratoParametrosValores(
            contrato_id=contrato.id,
            parametro_id=buscar_ou_criar_parametro(codigo).id,
            valor=valor
        )
        db.session.add(parametro)
    
    db.session.commit()
```

## 4. Serviço de Exportação

### ExportacaoService

**Responsabilidade:** Exportar contratos em diferentes formatos.

#### Métodos Principais

##### gerar_html_contrato(contrato_id)

Gera HTML do contrato para prévia.

```python
def gerar_html_contrato(contrato_id: int) -> str:
    """
    Gera HTML do contrato para prévia.
    
    Args:
        contrato_id: ID do contrato
        
    Returns:
        str: HTML do contrato
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    clausulas = ContratoClausulas.query.filter_by(
        contrato_id=contrato_id
    ).order_by(ContratoClausulas.ordem).all()
    
    # Template HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Contrato {contrato.serie}-{contrato.numero}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
            .cabecalho {{ text-align: center; margin-bottom: 40px; }}
            .qualificacao {{ margin-bottom: 30px; }}
            .clausula {{ margin-bottom: 20px; }}
            .clausula-titulo {{ font-weight: bold; margin-bottom: 10px; }}
            .assinaturas {{ margin-top: 50px; display: flex; justify-content: space-between; }}
            .assinatura {{ width: 45%; }}
        </style>
    </head>
    <body>
        <div class="cabecalho">
            <h1>CONTRATO DE PRESTAÇÃO DE SERVIÇOS</h1>
            <p>Número: {contrato.serie}-{contrato.numero}</p>
        </div>
        
        <div class="qualificacao">
            <h2>QUALIFICAÇÃO DAS PARTES</h2>
            <p><strong>CONTRATADA:</strong> {contrato.contratada.nome}, CNPJ {formatar_cnpj(contrato.contratada.cnpj_cpf)}, 
            estabelecida em {formatar_endereco_completo(contrato.contratada)}.</p>
            <p><strong>CONTRATANTE:</strong> {contrato.contratante.nome}, CNPJ/CPF {formatar_cnpj_cpf(contrato.contratante.cnpj_cpf)}, 
            estabelecido em {formatar_endereco_completo(contrato.contratante)}.</p>
        </div>
        
        <div class="clausulas">
    """
    
    # Adicionar cláusulas
    for clausula in clausulas:
        texto_com_placeholders = substituir_placeholders(clausula.texto, contrato)
        html += f"""
            <div class="clausula">
                <div class="clausula-titulo">{clausula.titulo}</div>
                <div class="clausula-texto">{texto_com_placeholders}</div>
            </div>
        """
    
    html += """
        </div>
        
        <div class="assinaturas">
            <div class="assinatura">
                <p>_____________________________</p>
                <p><strong>CONTRATADA</strong></p>
            </div>
            <div class="assinatura">
                <p>_____________________________</p>
                <p><strong>CONTRATANTE</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
```

##### gerar_pdf_contrato(contrato_id)

Gera PDF do contrato.

```python
def gerar_pdf_contrato(contrato_id: int) -> bytes:
    """
    Gera PDF do contrato.
    
    Args:
        contrato_id: ID do contrato
        
    Returns:
        bytes: Conteúdo do PDF
    """
    from weasyprint import HTML
    
    html = gerar_html_contrato(contrato_id)
    
    # Converter para PDF
    pdf = HTML(string=html).write_pdf()
    
    return pdf
```

##### gerar_docx_contrato(contrato_id)

Gera DOCX do contrato.

```python
def gerar_docx_contrato(contrato_id: int) -> bytes:
    """
    Gera DOCX do contrato.
    
    Args:
        contrato_id: ID do contrato
        
    Returns:
        bytes: Conteúdo do DOCX
    """
    from docx import Document
    
    contrato = Contrato.query.get_or_404(contrato_id)
    clausulas = ContratoClausulas.query.filter_by(
        contrato_id=contrato_id
    ).order_by(ContratoClausulas.ordem).all()
    
    doc = Document()
    
    # Título
    doc.add_heading('CONTRATO DE PRESTAÇÃO DE SERVIÇOS', 0)
    doc.add_paragraph(f'Número: {contrato.serie}-{contrato.numero}')
    
    # Qualificação das partes
    doc.add_heading('QUALIFICAÇÃO DAS PARTES', 1)
    doc.add_paragraph(f'CONTRATADA: {contrato.contratada.nome}, CNPJ {formatar_cnpj(contrato.contratada.cnpj_cpf)}')
    doc.add_paragraph(f'CONTRATANTE: {contrato.contratante.nome}, CNPJ/CPF {formatar_cnpj_cpf(contrato.contratante.cnpj_cpf)}')
    
    # Cláusulas
    for clausula in clausulas:
        doc.add_heading(clausula.titulo, 2)
        texto = substituir_placeholders(clausula.texto, contrato)
        doc.add_paragraph(texto)
    
    # Converter para bytes
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer.read()
```

## 5. Serviço de Histórico

### HistoricoService

**Responsabilidade:** Gerenciar histórico de alterações dos contratos.

#### Métodos Principais

##### registrar_historico_contrato(contrato, acao, user_id, **kwargs)

Registra uma alteração no histórico do contrato.

```python
def registrar_historico_contrato(contrato: Contrato, acao: str, user_id: int, **kwargs):
    """
    Registra uma alteração no histórico do contrato.
    
    Args:
        contrato: Objeto do contrato
        acao: Ação realizada ('criado', 'editado', 'assinado', 'cancelado', 'rescindido')
        user_id: ID do usuário
        **kwargs: Dados adicionais (status_anterior, campos_alterados, etc.)
    """
    # Buscar última versão
    ultima_versao = db.session.query(func.max(ContratoHistorico.versao)).filter_by(
        contrato_id=contrato.id
    ).scalar() or 0
    
    # Criar registro de histórico
    historico = ContratoHistorico(
        contrato_id=contrato.id,
        versao=ultima_versao + 1,
        acao=acao,
        status_anterior=kwargs.get('status_anterior'),
        status_novo=contrato.status,
        descricao_alteracao=kwargs.get('descricao_alteracao'),
        campos_alterados=kwargs.get('campos_alterados'),
        clausulas_alteradas=kwargs.get('clausulas_alteradas'),
        alterado_por_user_id=user_id
    )
    
    db.session.add(historico)
```

##### buscar_historico_contrato(contrato_id)

Busca o histórico de alterações de um contrato.

```python
def buscar_historico_contrato(contrato_id: int) -> List[ContratoHistorico]:
    """
    Busca o histórico de alterações de um contrato.
    
    Args:
        contrato_id: ID do contrato
        
    Returns:
        List[ContratoHistorico]: Lista de histórico
    """
    return ContratoHistorico.query.filter_by(
        contrato_id=contrato_id
    ).order_by(ContratoHistorico.versao.desc()).all()
```

## Endpoints da API REST

### Contratos

```
POST   /api/contratos/gerar-from-orcamento/:orcamento_id
GET    /api/contratos/:id
PUT    /api/contratos/:id
PATCH  /api/contratos/:id/status
GET    /api/contratos/:id/historico
GET    /api/contratos
DELETE /api/contratos/:id
```

### Cláusulas

```
POST   /api/clausulas-padrao
GET    /api/clausulas-padrao
GET    /api/clausulas-padrao/:id
PUT    /api/clausulas-padrao/:id
DELETE /api/clausulas-padrao/:id

GET    /api/contratos/:contrato_id/clausulas
POST   /api/contratos/:contrato_id/clausulas
PUT    /api/contratos/:contrato_id/clausulas/:clausula_id
DELETE /api/contratos/:contrato_id/clausulas/:clausula_id
POST   /api/contratos/:contrato_id/clausulas/reordenar
POST   /api/contratos/:contrato_id/clausulas/adicionar-biblioteca/:clausula_padrao_id
```

### Exportação

```
GET    /api/contratos/:id/exportar/html
GET    /api/contratos/:id/exportar/pdf
GET    /api/contratos/:id/exportar/docx
```

### Anexos

```
POST   /api/contratos/:contrato_id/anexos
GET    /api/contratos/:contrato_id/anexos
DELETE /api/contratos/:contrato_id/anexos/:anexo_id
GET    /api/contratos/:contrato_id/anexos/:anexo_id/download
```
