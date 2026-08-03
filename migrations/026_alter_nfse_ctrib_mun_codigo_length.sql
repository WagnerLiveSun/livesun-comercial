-- Aumentar tamanho da coluna codigo_tributacao_municipal para 12 caracteres
ALTER TABLE nfse_ctrib_mun_referencia 
MODIFY COLUMN codigo_tributacao_municipal VARCHAR(12) NOT NULL;
