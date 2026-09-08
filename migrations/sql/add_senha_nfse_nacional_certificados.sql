-- nfse_nacional_certificados: senha e binario do certificado (.pfx/.p12) por empresa/ambiente
-- Revisar antes de executar (colunas nullable, sem perda de dados).

ALTER TABLE nfse_nacional_certificados
ADD COLUMN senha VARCHAR(512) NULL;

ALTER TABLE nfse_nacional_certificados
ADD COLUMN arquivo_binario LONGBLOB NULL;
