-- Adicionar campos de regime tributário para NFS-e (Simples Nacional)
ALTER TABLE empresas ADD COLUMN op_simp_nac INT DEFAULT 3 AFTER email;
ALTER TABLE empresas ADD COLUMN reg_ap_trib_sn INT DEFAULT 1 AFTER op_simp_nac;
