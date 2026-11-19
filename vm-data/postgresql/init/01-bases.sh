#!/bin/bash
# staging et datamart appartiennent a etl (Spark ecrit dedans).
# powerbi peut seulement se connecter a datamart et lire ses tables.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<EOSQL
CREATE USER etl WITH PASSWORD '$ETL_PASSWORD';
CREATE USER powerbi WITH PASSWORD '$POWERBI_PASSWORD';
CREATE DATABASE staging OWNER etl;
CREATE DATABASE datamart OWNER etl;
REVOKE CONNECT ON DATABASE staging FROM PUBLIC;
REVOKE CONNECT ON DATABASE datamart FROM PUBLIC;
GRANT CONNECT ON DATABASE datamart TO powerbi;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname datamart <<EOSQL
GRANT USAGE ON SCHEMA public TO powerbi;
ALTER DEFAULT PRIVILEGES FOR ROLE etl IN SCHEMA public GRANT SELECT ON TABLES TO powerbi;
EOSQL
