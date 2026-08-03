ALTER TABLE nfse_nacional_emissoes
    ADD COLUMN servico_local_prestacao VARCHAR(20) NOT NULL DEFAULT 'emitente' AFTER valor_iss,
    ADD COLUMN tp_ret_issqn VARCHAR(2) NOT NULL DEFAULT '1' AFTER servico_local_prestacao;