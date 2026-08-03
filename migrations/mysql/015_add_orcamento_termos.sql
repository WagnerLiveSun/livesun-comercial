-- Adicionar campos de termos variáveis ao orçamento
ALTER TABLE orcamentos
ADD COLUMN validade_precos TEXT AFTER observacoes_internas,
ADD COLUMN condicoes_pagamento TEXT AFTER validade_precos,
ADD COLUMN termos_compra TEXT AFTER condicoes_pagamento,
ADD COLUMN detalhes_tecnicos TEXT AFTER termos_compra;
