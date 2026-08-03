-- Add senha column to nfse_nacional_certificados
-- Review before executing. This will add a nullable column to store certificate password.

ALTER TABLE nfse_nacional_certificados
ADD COLUMN senha VARCHAR(512) NULL;
