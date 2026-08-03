@echo off
set MYSQL_PWD=
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root comercial < "d:\App_LiveSun\LiveSun_Comercial_X\migrations\mysql\014_create_contratos_tables.sql"
