-- Aumentar tamanho da coluna codigo_tributacao_municipal para 12 caracteres
ALTER TABLE nfse_ctrib_mun_referencia 
ALTER COLUMN codigo_tributacao_municipal TYPE VARCHAR(12);
