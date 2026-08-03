-- Analise completa das tabelas de contratos no PostgreSQL
SELECT 
    'Tabelas de contratos' as tipo,
    tablename as nome,
    (xpath('/row/count/text()', query_to_xml(format('SELECT COUNT(*) FROM %I', tablename), false, true)))[1]::text::int as registros
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE '%contrato%'
ORDER BY tablename;
