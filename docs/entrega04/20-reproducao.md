# 20. Como reproduzir

O projeto roda com Docker e o gerenciador uv para Python. Os comandos abaixo são executados na raiz do repositório.

```bash
# 1. Bancos; a base original carrega sozinha no primeiro uso
docker compose up -d
PSQL="docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U pi -d northwind"
MONGO="docker compose exec -T mongo mongosh -u pi -p pi --authenticationDatabase admin --quiet"

# 2. Modelo relacional, índices, views e procedures
$PSQL -f /sql/10_ddl.sql
$PSQL -f /sql/20_load.sql
$PSQL -f /sql/30_indexes.sql
$PSQL -f /sql/entrega03/00_views.sql
$PSQL -f /sql/entrega03/10_procedures.sql

# 3. Documentos: extração em SQL, carga e índices no MongoDB
docker compose exec -T postgres psql -X -qAt -v ON_ERROR_STOP=1 -U pi -d northwind \
  -f /sql/entrega02/01_exportar_documentos.sql > mongo/entrega02/dados/documentos.ejson
$MONGO --file /mongo/entrega02/02_carregar.js
$MONGO --file /mongo/entrega02/03_indices.js

# 4. Conferências e medições
uv sync
uv run python etl/validar_analytics.py
uv run python etl/conferir_python.py
(cd etl && uv run python testar_analytics.py)
uv run python bench/entrega03.py
uv run python bench/entrega04.py
```

Cada consulta também pode ser executada sozinha: os arquivos sql/queries/QNN.sql no psql ou em qualquer cliente SQL, e os arquivos mongo/pipelines/PNN.js no mongosh.
