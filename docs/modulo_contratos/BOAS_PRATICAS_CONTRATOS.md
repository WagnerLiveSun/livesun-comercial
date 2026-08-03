# Boas Práticas - Módulo de Gestão de Contratos

## 1. Integridade de Dados

### Evitar Duplicação de Cadastros

**Problema:** Múltiplos cadastros da mesma entidade (empresa/cliente) podem causar inconsistências.

**Solução:**

```python
# Ao buscar entidade para contrato, usar busca fuzzy
def buscar_entidade_por_cnpj(cnpj_cpf: str, empresa_id: int) -> Entidade:
    """
    Busca entidade por CNPJ/CPF com validação de duplicidade.
    """
    # Normalizar CNPJ/CPF (remover caracteres especiais)
    cnpj_normalizado = re.sub(r'[^0-9]', '', cnpj_cpf)
    
    # Buscar existente
    entidade = Entidade.query.filter_by(
        empresa_id=empresa_id,
        cnpj_cpf=cnpj_normalizado
    ).first()
    
    if entidade:
        return entidade
    
    # Se não existe, alertar usuário
    raise ValueError(f"Entidade com CNPJ/CPF {cnpj_cpf} não encontrada. Cadastre primeiro.")
```

**Validação no cadastro de entidades:**

```python
# Antes de criar nova entidade, verificar duplicidade
def validar_duplicidade_entidade(dados: dict, empresa_id: int) -> bool:
    """
    Valida se não existe entidade duplicada.
    """
    cnpj_normalizado = re.sub(r'[^0-9]', '', dados.get('cnpj_cpf', ''))
    
    existente = Entidade.query.filter_by(
        empresa_id=empresa_id,
        cnpj_cpf=cnpj_normalizado
    ).first()
    
    if existente:
        raise ValueError(
            f"Já existe entidade com este CNPJ/CPF: {existente.nome} "
            f"(ID: {existente.id}). Use o cadastro existente."
        )
    
    return True
```

### Validação de Referências

**Garantir que orçamentos não sejam excluídos se tiverem contrato vinculado:**

```python
# No modelo Orcamento
class Orcamento(db.Model):
    # ... campos ...
    
    @property
    def possui_contrato_vinculado(self):
        return Contrato.query.filter_by(orcamento_id=self.id).first() is not None

# Ao excluir orçamento
def excluir_orcamento(orcamento_id: int):
    orcamento = Orcamento.query.get_or_404(orcamento_id)
    
    if orcamento.possui_contrato_vinculado:
        raise ValueError(
            "Não é possível excluir orçamento que possui contrato vinculado. "
            "Exclua o contrato primeiro."
        )
    
    db.session.delete(orcamento)
    db.session.commit()
```

---

## 2. Parametrização de Variáveis (Placeholders)

### Estrutura de Placeholders

**Usar sintaxe padronizada:**

```python
# Formato: {NOME_PARAMETRO}
# Exemplos:
{CONTRATADA_RAZAO_SOCIAL}
{CONTRATANTE_CNPJ_CPF}
{CONTRATO_VALOR_TOTAL}
{CONTRATO_DATA_INICIO}
```

### Validação de Placeholders

**Verificar se todos os placeholders foram substituídos:**

```python
def validar_placeholders_substituidos(texto: str, contrato_id: int) -> List[str]:
    """
    Valida se todos os placeholders foram substituídos.
    Retorna lista de placeholders não substituídos.
    """
    import re
    
    # Buscar todos os placeholders no texto
    placeholders = re.findall(r'\{([^}]+)\}', texto)
    
    # Buscar valores disponíveis
    valores = buscar_valores_parametros(contrato_id)
    
    # Identificar não substituídos
    nao_substituidos = [p for p in placeholders if p not in valores]
    
    return nao_substituidos

# Ao salvar contrato
def salvar_contrato(contrato_id: int):
    contrato = Contrato.query.get_or_404(contrato_id)
    
    for clausula in contrato.clausulas:
        nao_substituidos = validar_placeholders_substituidos(clausula.texto, contrato_id)
        
        if nao_substituidos:
            raise ValueError(
                f"Cláusula '{clausula.titulo}' possui placeholders não substituídos: "
                f"{', '.join(nao_substituidos)}"
            )
```

### Hierarquia de Substituição

**Ordem de prioridade para valores de placeholders:**

1. **Valores específicos do contrato** (contrato_parametros_valores)
2. **Valores do orçamento vinculado**
3. **Valores da entidade (cliente/empresa)**
4. **Valores padrão do sistema**

```python
def buscar_valor_placeholder(codigo: str, contrato: Contrato) -> str:
    """
    Busca valor de placeholder com hierarquia de prioridade.
    """
    # 1. Valores específicos do contrato
    valor_especifico = ContratoParametrosValores.query.filter_by(
        contrato_id=contrato.id,
        parametro_codigo=codigo
    ).first()
    
    if valor_especifico:
        return valor_especifico.valor
    
    # 2. Valores do orçamento
    if contrato.orcamento:
        valor_orcamento = buscar_valor_orcamento(codigo, contrato.orcamento)
        if valor_orcamento:
            return valor_orcamento
    
    # 3. Valores da entidade
    if codigo.startswith('CONTRATADA_'):
        valor_entidade = buscar_valor_entidade(codigo, contrato.contratada)
        if valor_entidade:
            return valor_entidade
    elif codigo.startswith('CONTRATANTE_'):
        valor_entidade = buscar_valor_entidade(codigo, contrato.contratante)
        if valor_entidade:
            return valor_entidade
    
    # 4. Valores padrão
    parametro_padrao = ContratoParametros.query.filter_by(codigo=codigo).first()
    if parametro_padrao:
        return parametro_padrao.valor_padrao or ''
    
    # 5. Retornar placeholder original se não encontrado
    return f'{{{codigo}}}'
```

### Placeholders Condicionais

**Suporte a lógica condicional no texto:**

```python
# Sintaxe: {IF:CONDICAO}texto{ENDIF}
# Exemplo: {IF:CONTRATO_VALOR_MENSAL}Mensal: {CONTRATO_VALOR_MENSAL}{ENDIF}

def processar_placeholders_condicionais(texto: str, contrato: Contrato) -> str:
    """
    Processa placeholders condicionais.
    """
    import re
    
    # Buscar blocos condicionais
    padrao = r'\{IF:([^}]+)\}(.*?)\{ENDIF\}'
    
    def substituir_condicional(match):
        condicao = match.group(1)
        conteudo = match.group(2)
        
        # Buscar valor da condição
        valor = buscar_valor_placeholder(condicao, contrato)
        
        # Se valor existe e não está vazio, retorna conteúdo
        if valor and valor != f'{{{condicao}}}':
            return substituir_placeholders(conteudo, contrato)
        
        # Caso contrário, retorna vazio
        return ''
    
    # Processar todos os blocos condicionais
    texto = re.sub(padrao, substituir_condicional, texto, flags=re.DOTALL)
    
    return texto
```

---

## 3. Preparação para Integração

### Estrutura de Dados para Faturamento

**Campos estruturados no contrato para automação:**

```python
class Contrato(db.Model):
    # ... campos existentes ...
    
    # Campos para integração com faturamento
    faturamento_automatico = db.Column(db.Boolean, default=True)
    dia_vencimento_fatura = db.Column(db.Integer, default=5)  # Dia do mês
    antecedencia_envio_boleto = db.Column(db.Integer, default=5)  # Dias antes
    
    # Campos para integração com financeiro
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'))
    plano_conta_receita_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'))
    
    # Campos para integração com serviços
    gestor_projeto_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    equipe_tecnica_ids = db.Column(db.JSON)  # Lista de IDs de técnicos
```

### Gatilhos para Integração

**Evento de assinatura do contrato:**

```python
def on_contrato_assinado(contrato_id: int):
    """
    Gatilho executado quando contrato é assinado.
    Integra com faturamento, financeiro e gestão de serviços.
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    
    # 1. Criar assinatura no módulo de cobrança
    if contrato.faturamento_automatico:
        criar_assinatura_cobranca(contrato)
    
    # 2. Criar lançamentos financeiros recorrentes
    if contrato.periodicidade in ['mensal', 'trimestral', 'semestral', 'anual']:
        criar_lancamentos_recorrentes(contrato)
    
    # 3. Criar projeto/ordem de serviço
    criar_projeto_servico(contrato)
    
    # 4. Notificar equipe técnica
    notificar_equipe_tecnica(contrato)
```

### Integração com Faturamento Recorrente

```python
def criar_assinatura_cobranca(contrato: Contrato):
    """
    Cria assinatura no módulo de cobrança recorrente.
    """
    from modules.cobranca.models import AssinaturaEmpresa, CatalogoPlanosComercial
    
    # Buscar ou criar plano compatível
    plano = buscar_plano_compativel(contrato)
    
    # Criar assinatura
    assinatura = AssinaturaEmpresa(
        empresa_id=contrato.empresa_id,
        cliente_id=contrato.cliente_id,
        plano_id=plano.id,
        contrato_id=contrato.id,
        valor_mensal=contrato.valor_mensal,
        data_inicio=contrato.data_inicio_vigencia,
        data_fim=contrato.data_fim_vigencia,
        status='ativa'
    )
    
    db.session.add(assinatura)
    db.session.commit()
```

### Integração com Financeiro

```python
def criar_lancamentos_recorrentes(contrato: Contrato):
    """
    Cria lançamentos financeiros recorrentes.
    """
    from modules.financeiro.models import Lancamento
    
    # Calcular quantidade de parcelas
    meses = calcular_meses_vigencia(
        contrato.data_inicio_vigencia,
        contrato.data_fim_vigencia
    )
    
    # Criar lançamentos mensais
    data_vencimento = contrato.data_inicio_vigencia
    data_vencimento = data_vencimento.replace(day=contrato.dia_vencimento_fatura)
    
    for i in range(meses):
        lancamento = Lancamento(
            empresa_id=contrato.empresa_id,
            entidade_id=contrato.cliente_id,
            fluxo_conta_id=contrato.plano_conta_receita_id,
            conta_banco_id=contrato.conta_banco_id,
            data_evento=data_vencimento,
            data_vencimento=data_vencimento,
            valor_real=contrato.valor_mensal,
            status='aberto',
            referencia_banco=f'CTR-{contrato.numero}',
            fonte='contrato_recorrente',
            contrato_id=contrato.id
        )
        
        db.session.add(lancamento)
        
        # Avançar para próximo mês
        data_vencimento = avancar_mes(data_vencimento, contrato.periodicidade)
    
    db.session.commit()
```

### Integração com Gestão de Serviços

```python
def criar_projeto_servico(contrato: Contrato):
    """
    Cria projeto/ordem de serviço para o contrato.
    """
    from modules.servicos.models import Projeto
    
    projeto = Projeto(
        empresa_id=contrato.empresa_id,
        cliente_id=contrato.cliente_id,
        contrato_id=contrato.id,
        titulo=f'Serviços - {contrato.contratante.nome}',
        descricao=contrato.descricao_servicos,
        data_inicio=contrato.data_inicio_vigencia,
        data_fim=contrato.data_fim_vigencia,
        gestor_id=contrato.gestor_projeto_id,
        status='em_andamento'
    )
    
    db.session.add(projeto)
    db.session.commit()
    
    # Atribuir equipe técnica
    if contrato.equipe_tecnica_ids:
        for user_id in contrato.equipe_tecnica_ids:
            atribuir_equipe_projeto(projeto.id, user_id)
```

---

## 4. Controle de Permissões

### Níveis de Acesso

**Definir permissões específicas para o módulo:**

```python
# Permissões do módulo de contratos
PERMISSOES_CONTRATOS = [
    'contratos.view',           # Visualizar contratos
    'contratos.create',         # Criar contratos
    'contratos.edit',           # Editar contratos (rascunho)
    'contratos.edit_signed',    # Editar contratos assinados (admin apenas)
    'contratos.delete',         # Excluir contratos (rascunho)
    'contratos.delete_signed',  # Excluir contratos assinados (admin apenas)
    'contratos.sign',           # Assinar contratos
    'contratos.export',         # Exportar contratos
    'clausulas.view',           # Visualizar cláusulas padrão
    'clausulas.create',         # Criar cláusulas padrão
    'clausulas.edit',           # Editar cláusulas padrão
    'clausulas.delete',         # Excluir cláusulas padrão
    'clausulas.edit_critical',  # Editar cláusulas críticas (admin apenas)
]
```

### Validação de Permissões

```python
def verificar_permissao_clausula(clausula: ContratoClausulas, user: User, acao: str) -> bool:
    """
    Valida se usuário tem permissão para editar cláusula.
    """
    # Cláusulas obrigatórias não editáveis
    if clausula.obrigatoria and not clausula.editavel:
        if not user.has_permission('clausulas.edit_critical'):
            return False
    
    # Cláusulas críticas (ex: vínculo trabalhista)
    if clausula.titulo in ['VÍNCULO TRABALHISTA', 'FORO']:
        if not user.has_permission('clausulas.edit_critical'):
            return False
    
    return True
```

### Auditoria de Ações

**Registrar todas as ações críticas:**

```python
def registrar_auditoria_contrato(contrato_id: int, acao: str, user_id: int, detalhes: dict = None):
    """
    Registra ação de auditoria.
    """
    from modules.auditoria.models import AuditoriaEventos
    
    AuditoriaEventos.create(
        empresa_id=current_user.empresa_id,
        user_id=user_id,
        modulo='contratos',
        acao=acao,
        entidade='contrato',
        entidade_id=str(contrato_id),
        detalhes=detalhes or {},
        ip_origem=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
```

---

## 5. Versionamento e Histórico

### Snapshot Completo do Contrato

**Armazenar snapshot JSON do contrato em cada versão:**

```python
def criar_snapshot_contrato(contrato: Contrato) -> dict:
    """
    Cria snapshot completo do contrato para histórico.
    """
    snapshot = {
        'contrato': {
            'id': contrato.id,
            'numero': contrato.numero,
            'status': contrato.status,
            'valor_total': str(contrato.valor_total),
            'valor_mensal': str(contrato.valor_mensal),
            'forma_pagamento': contrato.forma_pagamento,
            'periodicidade': contrato.periodicidade,
            'data_inicio_vigencia': contrato.data_inicio_vigencia.isoformat(),
            'data_fim_vigencia': contrato.data_fim_vigencia.isoformat() if contrato.data_fim_vigencia else None,
            'descricao_servicos': contrato.descricao_servicos,
        },
        'clausulas': []
    }
    
    for clausula in contrato.clausulas:
        snapshot['clausulas'].append({
            'id': clausula.id,
            'titulo': clausula.titulo,
            'texto': clausula.texto,
            'ordem': clausula.ordem,
            'editavel': clausula.editavel,
            'obrigatoria': clausula.obrigatoria
        })
    
    return snapshot

# Ao salvar alteração
def salvar_alteracao_contrato(contrato_id: int, alteracoes: dict, user_id: int):
    contrato = Contrato.query.get_or_404(contrato_id)
    
    # Criar snapshot antes de alterar
    snapshot_anterior = criar_snapshot_contrato(contrato)
    
    # Aplicar alterações
    # ... código de alteração ...
    
    # Criar snapshot após alterar
    snapshot_novo = criar_snapshot_contrato(contrato)
    
    # Registrar histórico com snapshots
    historico = ContratoHistorico(
        contrato_id=contrato.id,
        versao=contrato.versao + 1,
        acao='editado',
        status_anterior=snapshot_anterior['contrato']['status'],
        status_novo=snapshot_novo['contrato']['status'],
        campos_alterados=list(alteracoes.keys()),
        alterado_por_user_id=user_id,
        snapshot_contrato={
            'anterior': snapshot_anterior,
            'novo': snapshot_novo
        }
    )
    
    db.session.add(historico)
    db.session.commit()
```

### Restauração de Versão

**Permitir restaurar versão anterior (apenas para rascunhos):**

```python
def restaurar_versao_contrato(contrato_id: int, versao: int, user_id: int):
    """
    Restaura contrato para versão específica.
    """
    contrato = Contrato.query.get_or_404(contrato_id)
    
    # Validar status
    if contrato.status != 'rascunho':
        raise ValueError("Apenas contratos em rascunho podem ser restaurados")
    
    # Buscar versão
    historico = ContratoHistorico.query.filter_by(
        contrato_id=contrato_id,
        versao=versao
    ).first_or_404()
    
    # Restaurar dados
    snapshot = historico.snapshot_contrato['anterior']
    
    # Restaurar dados do contrato
    contrato.valor_total = Decimal(snapshot['contrato']['valor_total'])
    contrato.valor_mensal = Decimal(snapshot['contrato']['valor_mensal'])
    contrato.forma_pagamento = snapshot['contrato']['forma_pagamento']
    # ... outros campos ...
    
    # Restaurar cláusulas
    ContratoClausulas.query.filter_by(contrato_id=contrato_id).delete()
    
    for clausula_data in snapshot['clausulas']:
        clausula = ContratoClausulas(
            contrato_id=contrato.id,
            clausula_padrao_id=clausula_data.get('clausula_padrao_id'),
            titulo=clausula_data['titulo'],
            texto=clausula_data['texto'],
            ordem=clausula_data['ordem'],
            editavel=clausula_data['editavel'],
            obrigatoria=clausula_data['obrigatoria']
        )
        db.session.add(clausula)
    
    # Registrar restauração
    registrar_historico_contrato(
        contrato,
        'restaurado',
        user_id,
        descricao_alteracao=f'Restaurado para versão {versao}'
    )
    
    db.session.commit()
```

---

## 6. Performance e Escalabilidade

### Índices Obrigatórios

```sql
-- Índices para performance
CREATE INDEX idx_contratos_cliente_status ON contratos(cliente_id, status);
CREATE INDEX idx_contratos_vigencia ON contratos(data_inicio_vigencia, data_fim_vigencia);
CREATE INDEX idx_contrato_clausulas_contrato_ordem ON contrato_clausulas(contrato_id, ordem);
CREATE INDEX idx_contrato_historico_contrato_versao ON contrato_historico(contrato_id, versao);
```

### Cache de Cláusulas Padrão

**Cláusulas padrão mudam raramente, usar cache:**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def buscar_clausulas_padrao_cache(empresa_id: int, tipo: str = None):
    """
    Busca cláusulas padrão com cache.
    """
    query = ClausulaContratoPadrao.query.filter_by(
        empresa_id=empresa_id,
        ativo=True
    )
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    return query.order_by(ClausulaContratoPadrao.ordem_padrao).all()

# Invalidar cache ao alterar cláusula
def atualizar_clausula_padrao(clausula_id: int, dados: dict, user_id: int):
    clausula = ClausulaContratoPadrao.query.get_or_404(clausula_id)
    
    # Atualizar
    for campo, valor in dados.items():
        setattr(clausula, campo, valor)
    
    clausula.atualizado_em = datetime.utcnow()
    clausula.atualizado_por_user_id = user_id
    
    # Invalidar cache
    buscar_clausulas_padrao_cache.cache_clear()
    
    db.session.commit()
```

### Paginação de Listas

**Usar paginação em listas grandes:**

```python
from flask_sqlalchemy.pagination import Pagination

def listar_contratos_paginados(empresa_id: int, pagina: int = 1, por_pagina: int = 20):
    """
    Lista contratos com paginação.
    """
    query = Contrato.query.filter_by(empresa_id=empresa_id)
    
    return Pagination(
        query=query,
        page=pagina,
        per_page=por_pagina,
        error_out=False
    )
```

---

## 7. Segurança

### Validação de Entrada

**Sanitizar todo texto de cláusulas:**

```python
from bleach import clean

def sanitizar_texto_clausula(texto: str) -> str:
    """
    Sanitiza texto de cláusula para evitar XSS.
    """
    # Permitir apenas tags HTML seguras
    tags_permitidas = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
    atributos_permitidos = {}
    
    return clean(texto, tags=tags_permitidas, attributes=atributos_permitidos)
```

### Criptografia de Dados Sensíveis

**Se houver dados sensíveis nos contratos:**

```python
from cryptography.fernet import Fernet

def criptografar_dado_sensivel(dado: str) -> str:
    """
    Criptografa dado sensível.
    """
    chave = os.environ.get('ENCRYPTION_KEY')
    fernet = Fernet(chave.encode())
    
    return fernet.encrypt(dado.encode()).decode()

def descriptografar_dado_sensivel(dado_criptografado: str) -> str:
    """
    Descriptografa dado sensível.
    """
    chave = os.environ.get('ENCRYPTION_KEY')
    fernet = Fernet(chave.encode())
    
    return fernet.decrypt(dado_criptografado.encode()).decode()
```

---

## 8. Testes

### Testes Unitários

```python
def test_gerar_contrato_from_orcamento():
    """Testa geração de contrato a partir de orçamento."""
    # Setup
    orcamento = criar_orcamento_teste(status='aprovado')
    
    # Act
    contrato = ContratoService.gerar_contrato_from_orcamento(orcamento.id, user_id=1)
    
    # Assert
    assert contrato.status == 'rascunho'
    assert contrato.orcamento_id == orcamento.id
    assert len(contrato.clausulas) > 0

def test_substituir_placeholders():
    """Testa substituição de placeholders."""
    texto = "Valor: {CONTRATO_VALOR_TOTAL}"
    contrato = criar_contrato_teste(valor_total=Decimal('5000.00'))
    
    resultado = PlaceholderService.substituir_placeholders(texto, contrato)
    
    assert "R$ 5.000,00" in resultado

def test_clausula_obrigatoria_nao_pode_ser_removida():
    """Testa que cláusula obrigatória não pode ser removida."""
    contrato = criar_contrato_teste()
    clausula = contrato.clausulas[0]
    clausula.obrigatoria = True
    
    with pytest.raises(ValueError):
        ClausulaService.remover_clausula_contrato(clausula.id, user_id=1)
```

### Testes de Integração

```python
def test_integracao_faturamento_ao_assinar():
    """Testa integração com faturamento ao assinar contrato."""
    contrato = criar_contrato_teste(status='rascunho')
    contrato.faturamento_automatico = True
    
    # Assinar contrato
    ContratoService.alterar_status_contrato(contrato.id, 'assinado', user_id=1)
    
    # Verificar se assinatura foi criada
    assinatura = AssinaturaEmpresa.query.filter_by(contrato_id=contrato.id).first()
    assert assinatura is not None
    assert assinatura.status == 'ativa'
```

---

## 9. Monitoramento e Logs

### Logging de Operações Críticas

```python
import logging

logger = logging.getLogger('contratos')

def gerar_contrato_from_orcamento(orcamento_id: int, user_id: int):
    logger.info(
        f"Iniciando geração de contrato para orçamento {orcamento_id} "
        f"pelo usuário {user_id}"
    )
    
    try:
        contrato = ContratoService.gerar_contrato_from_orcamento(orcamento_id, user_id)
        logger.info(f"Contrato {contrato.id} gerado com sucesso")
        return contrato
    except Exception as e:
        logger.error(
            f"Erro ao gerar contrato para orçamento {orcamento_id}: {str(e)}",
            exc_info=True
        )
        raise
```

### Métricas de Uso

```python
def registrar_metrica_contrato_gerado(tempo_segundos: float):
    """
    Registra métrica de tempo de geração de contrato.
    """
    from prometheus_client import Histogram
    
    histogram = Histogram('contrato_geracao_tempo', 'Tempo de geração de contrato')
    histogram.observe(tempo_segundos)
```

---

## 10. Checklist de Implementação

### Fase 1: Estrutura de Dados
- [ ] Criar tabelas do banco de dados
- [ ] Criar modelos SQLAlchemy
- [ ] Criar migrações
- [ ] Implementar índices de performance

### Fase 2: Serviços de Negócio
- [ ] Implementar ContratoService
- [ ] Implementar ClausulaService
- [ ] Implementar PlaceholderService
- [ ] Implementar ExportacaoService
- [ ] Implementar HistoricoService

### Fase 3: APIs REST
- [ ] Criar endpoints de contratos
- [ ] Criar endpoints de cláusulas
- [ ] Criar endpoints de exportação
- [ ] Implementar autenticação e autorização
- [ ] Implementar validação de entrada

### Fase 4: Interface do Usuário
- [ ] Criar tela de cadastro de cláusulas
- [ ] Criar tela de edição de contrato
- [ ] Implementar editor rich text
- [ ] Implementar drag & drop de cláusulas
- [ ] Criar tela de listagem de contratos
- [ ] Implementar prévia HTML/PDF

### Fase 5: Integrações
- [ ] Integrar com módulo de faturamento
- [ ] Integrar com módulo financeiro
- [ ] Integrar com módulo de serviços
- [ ] Implementar gatilhos de eventos

### Fase 6: Testes e Qualidade
- [ ] Escrever testes unitários
- [ ] Escrever testes de integração
- [ ] Implementar logging
- [ ] Implementar monitoramento
- [ ] Fazer revisão de segurança

### Fase 7: Documentação
- [ ] Documentar API
- [ ] Documentar modelo de dados
- [ ] Criar manual do usuário
- [ ] Criar guia de instalação
