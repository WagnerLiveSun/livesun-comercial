# Script para verificar tabelas criadas no PostgreSQL
$env:PGPASSWORD='livesun'
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d comercial -c "\dt" -o "resultado_tabelas.txt"
Write-Host "Resultado salvo em resultado_tabelas.txt"
Get-Content resultado_tabelas.txt
