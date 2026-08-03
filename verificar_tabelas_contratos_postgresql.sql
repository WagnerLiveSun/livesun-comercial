SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%contrato%' ORDER BY tablename;
