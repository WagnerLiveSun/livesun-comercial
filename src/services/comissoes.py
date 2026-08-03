"""
Serviço de Comissões - Apuração, cálculo e gerenciamento de comissões
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import and_, func
from src.models import db, Lancamento, Entidade, Comissao, ParametroSistema
import logging

logger = logging.getLogger(__name__)


class ServicoComissoes:
    """Serviço para operações de comissões"""
    
    @staticmethod
    def obter_aliquota_padrao(empresa_id: int) -> Decimal:
        """
        Obtém a alíquota padrão de comissão do sistema.
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Alíquota padrão em percentual (ex: 5.00)
        """
        param = ParametroSistema.query.filter_by(
            empresa_id=empresa_id,
            chave='aliquota_comissao_padrao'
        ).first()
        
        if param:
            try:
                return Decimal(param.valor)
            except (ValueError, TypeError):
                logger.warning(f"Alíquota padrão inválida: {param.valor}. Usando 0.00")
                return Decimal('0.00')
        return Decimal('0.00')
    
    @staticmethod
    def calcular_valor_liquido(lancamento: Lancamento, entidade_cliente: Entidade) -> Decimal:
        """
        Calcula o valor líquido base para comissão.
        
        Fórmula: vl_liquido = vl_nota - vl_imposto - vl_outros_custos - vl_repasse
        
        Args:
            lancamento: Registro de lançamento
            entidade_cliente: Entidade do tipo CLIENTE
            
        Returns:
            Valor líquido em Decimal
        """
        vl_nota = Decimal(str(lancamento.valor_real or 0))
        vl_imposto = Decimal(str(lancamento.valor_imposto or 0))
        vl_outros_custos = Decimal(str(lancamento.valor_outros_custos or 0))
        vl_repasse = Decimal(str(entidade_cliente.valor_repasse or 0))
        
        vl_liquido = vl_nota - vl_imposto - vl_outros_custos - vl_repasse
        
        # Garantir que não seja negativo
        return max(vl_liquido, Decimal('0.00'))
    
    @staticmethod
    def obter_aliquota_aplicavel(entidade_cliente: Entidade, empresa_id: int) -> Decimal:
        """
        Determina qual alíquota deve ser aplicada.
        
        Usa alíquota específica do cliente se houver, senão usa padrão do sistema.
        
        Args:
            entidade_cliente: Entidade do tipo CLIENTE
            empresa_id: ID da empresa para buscar padrão
            
        Returns:
            Alíquota em percentual
        """
        if entidade_cliente.aliquota_comissao_especifica:
            return Decimal(str(entidade_cliente.aliquota_comissao_especifica))
        
        return ServicoComissoes.obter_aliquota_padrao(empresa_id)
    
    @staticmethod
    def calcular_comissao(vl_liquido: Decimal, aliquota: Decimal) -> Decimal:
        """
        Calcula o valor da comissão.
        
        Fórmula: vl_comissao = vl_liquido × (alíquota / 100)
        
        Args:
            vl_liquido: Valor líquido
            aliquota: Alíquota em percentual (ex: 5.00)
            
        Returns:
            Valor da comissão
        """
        if vl_liquido <= 0:
            return Decimal('0.00')
        
        aliquota_decimal = aliquota / Decimal('100')
        comissao = vl_liquido * aliquota_decimal
        
        return comissao.quantize(Decimal('0.01'))
    
    @staticmethod
    def _validar_lancamento_empresa(lancamento_id: int, empresa_id: int) -> bool:
        """
        Valida se um lançamento pertence à empresa especificada.
        Segurança: previne acesso a lançamentos de outras empresas.
        """
        if not lancamento_id or not empresa_id:
            return False
        lancamento = Lancamento.query.filter_by(
            id=lancamento_id,
            empresa_id=empresa_id
        ).first()
        return lancamento is not None

    @staticmethod
    def lancamento_ja_apurado(lancamento_id: int, cliente_id: int, vendedor_id: int, empresa_id: int) -> bool:
        """
        Verifica se um lançamento já foi apurado em comissão.
        
        Args:
            lancamento_id: ID do lançamento
            cliente_id: ID da entidade cliente
            vendedor_id: ID da entidade vendedor
            empresa_id: ID da empresa
            
        Returns:
            True se já foi apurado, False caso contrário
        """
        # Validação de segurança: garantir que o lançamento pertence à empresa
        if not ServicoComissoes._validar_lancamento_empresa(lancamento_id, empresa_id):
            logger.warning(f"Tentativa de verificar apuração de lançamento {lancamento_id} não pertencente à empresa {empresa_id}")
            return False

        comissao = Comissao.query.filter_by(
            empresa_id=empresa_id,
            lancamento_id=lancamento_id,
            entidade_cliente_id=cliente_id,
            entidade_vendedor_id=vendedor_id,
            situacao='ativo'
        ).first()
        
        return comissao is not None
    
    @staticmethod
    def apurar_comissoes(
        empresa_id: int,
        data_inicio,
        data_fim,
        vendedor_id: int = None,
        cliente_id: int = None
    ) -> dict:
        """
        Executa a apuração de comissões para um período.
        
        Args:
            empresa_id: ID da empresa
            data_inicio: Data inicial (data_pagamento)
            data_fim: Data final (data_pagamento)
            vendedor_id: ID do vendedor (opcional)
            cliente_id: ID do cliente (opcional)
            
        Returns:
            Dict com resultado e estatísticas da apuração
        """
        inicio_msg = f"Iniciando apuração de comissões: {data_inicio} a {data_fim}"
        logger.info(inicio_msg)

        resultado = {
            'sucesso': True,
            'mensagem': '',
            'total_comissoes': Decimal('0.00'),
            'registros_criados': 0
        }

        try:
            # Gerar novo ID de apuração (sequence)
            max_apuracao = db.session.query(func.max(Comissao.id_apuracao)).filter_by(
                empresa_id=empresa_id
            ).scalar() or 0
            id_apuracao = max_apuracao + 1
            
            # Construir query de lançamentos elegíveis
            query = Lancamento.query.filter(
                Lancamento.empresa_id == empresa_id,
                Lancamento.data_pagamento.isnot(None),
                Lancamento.data_pagamento >= data_inicio,
                Lancamento.data_pagamento <= data_fim,
                Lancamento.status == 'pago'  # Apenas lançamentos pagos
            )
            
            # Aplicar filtros opcionais
            if cliente_id:
                query = query.filter(Lancamento.entidade_id == cliente_id)
            
            lancamentos = query.all()
            
            total_lancamentos_processados = 0
            total_comissao = Decimal('0.00')
            
            for lancamento in lancamentos:
                # Validar se entidade é CLIENTE
                if lancamento.entidade.tipo != 'C':
                    continue
                
                # Obter vendedor do cliente ou fallback para entidade_vendedor_padrao
                vendedor = lancamento.entidade.vendedor or getattr(lancamento.entidade, 'entidade_vendedor_padrao', None)
                if not vendedor:
                    logger.warning(f"Lançamento {lancamento.id} sem vendedor definido")
                    continue
                
                if vendedor_id and vendedor.id != vendedor_id:
                    continue
                
                # Remove comissões anteriores deste lançamento (se houver)
                Comissao.query.filter_by(
                    empresa_id=empresa_id,
                    lancamento_id=lancamento.id,
                    entidade_cliente_id=lancamento.entidade_id,
                    entidade_vendedor_id=vendedor.id,
                    situacao='ativo'
                ).delete()
                db.session.flush()
                
                # Calcular comissão
                vl_liquido = ServicoComissoes.calcular_valor_liquido(
                    lancamento,
                    lancamento.entidade
                )
                
                aliquota = ServicoComissoes.obter_aliquota_aplicavel(
                    lancamento.entidade,
                    empresa_id
                )
                
                vl_comissao = ServicoComissoes.calcular_comissao(vl_liquido, aliquota)
                
                # Calcular valor de repasse
                vl_repasse = Decimal(str(lancamento.entidade.valor_repasse or 0))
                
                # Criar registro de comissão
                comissao = Comissao(
                    empresa_id=empresa_id,
                    id_apuracao=id_apuracao,
                    lancamento_id=lancamento.id,
                    entidade_cliente_id=lancamento.entidade_id,
                    entidade_vendedor_id=vendedor.id,
                    dt_lancamento=lancamento.data_evento,
                    dt_vencimento=lancamento.data_vencimento,
                    dt_pagamento_recebimento=lancamento.data_pagamento,
                    vl_nota=Decimal(str(lancamento.valor_real or 0)),
                    vl_imposto=Decimal(str(lancamento.valor_imposto or 0)),
                    vl_outros_custos=Decimal(str(lancamento.valor_outros_custos or 0)),
                    vl_repasse=vl_repasse,
                    vl_liquido=vl_liquido,
                    aliquota_aplicada=aliquota,
                    vl_comissao=vl_comissao,
                    situacao='ativo'
                )
                
                db.session.add(comissao)
                total_lancamentos_processados += 1
                total_comissao += vl_comissao
                
                logger.info(f"Comissão calculada: Lancamento {lancamento.id} - "
                          f"Valor: R$ {vl_comissao}")
            
            # Commit da transação
            db.session.commit()

            resultado['registros_criados'] = total_lancamentos_processados
            resultado['total_comissoes'] = total_comissao
            resultado['mensagem'] = f"Apuração concluída. {total_lancamentos_processados} registros criados. Total comissões: R$ {total_comissao}"
            logger.info(resultado['mensagem'])

        except Exception as e:
            db.session.rollback()
            resultado['sucesso'] = False
            resultado['mensagem'] = f"Erro na apuração: {str(e)}"
            logger.error(resultado['mensagem'], exc_info=True)

        return resultado
    
    @staticmethod
    def obter_comissoes_filtradas(
        empresa_id: int,
        data_inicio=None,
        data_fim=None,
        vendedor_id: int = None,
        cliente_id: int = None,
        id_apuracao: int = None
    ):
        """
        Obtém comissões com filtros aplicados.
        
        Args:
            empresa_id: ID da empresa
            data_inicio: Data inicial de pagamento_recebimento
            data_fim: Data final de pagamento_recebimento
            vendedor_id: ID do vendedor
            cliente_id: ID do cliente
            id_apuracao: ID da apuração específica
            
        Returns:
            Query de comissões filtradas
        """
        query = Comissao.query.filter_by(empresa_id=empresa_id, situacao='ativo')
        
        if id_apuracao:
            query = query.filter_by(id_apuracao=id_apuracao)
        
        if data_inicio:
            query = query.filter(Comissao.dt_pagamento_recebimento >= data_inicio)
        
        if data_fim:
            query = query.filter(Comissao.dt_pagamento_recebimento <= data_fim)
        
        if vendedor_id:
            query = query.filter_by(entidade_vendedor_id=vendedor_id)
        
        if cliente_id:
            query = query.filter_by(entidade_cliente_id=cliente_id)
        
        return query
    
    @staticmethod
    def obter_resumo_por_vendedor(
        empresa_id: int,
        data_inicio=None,
        data_fim=None,
        vendedor_id: int = None,
        cliente_id: int = None
    ) -> list:
        """
        Obtém resumo de comissões agrupadas por vendedor.
        
        Args:
            empresa_id: ID da empresa
            data_inicio: Data inicial
            data_fim: Data final
            vendedor_id: ID do vendedor (filtro)
            cliente_id: ID do cliente (filtro)
            
        Returns:
            Lista de dicts com resumo por vendedor
        """
        query = ServicoComissoes.obter_comissoes_filtradas(
            empresa_id,
            data_inicio,
            data_fim,
            vendedor_id,
            cliente_id
        )
        
        comissoes = query.all()
        
        # Agrupar por vendedor
        # Carregar todos os vendedores em um dicionário para acesso rápido
        vendedor_ids = set(c.entidade_vendedor_id for c in comissoes)
        vendedores = Entidade.query.filter(Entidade.id.in_(vendedor_ids)).all()
        vendedores_dict = {v.id: v for v in vendedores}

        resumo = {}
        for comissao in comissoes:
            vendedor_id = comissao.entidade_vendedor_id
            vendedor = vendedores_dict.get(vendedor_id)
            if vendedor_id not in resumo:
                resumo[vendedor_id] = {
                    'vendedor': vendedor,  # Objeto Entidade
                    'total_notas': Decimal('0.00'),
                    'total_repasse': Decimal('0.00'),
                    'total_liquido': Decimal('0.00'),
                    'total_comissoes': Decimal('0.00'),
                    'quantidade_lancamentos': 0,
                    'comissoes': []
                }
            resumo[vendedor_id]['total_notas'] += comissao.vl_nota
            resumo[vendedor_id]['total_repasse'] += comissao.vl_repasse
            resumo[vendedor_id]['total_liquido'] += comissao.vl_liquido
            resumo[vendedor_id]['total_comissoes'] += comissao.vl_comissao
            resumo[vendedor_id]['quantidade_lancamentos'] += 1
            resumo[vendedor_id]['comissoes'].append(comissao)
        return list(resumo.values())