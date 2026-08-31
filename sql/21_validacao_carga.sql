-- =============================================================================
-- 21_validacao_carga.sql — a carga public -> nw preservou tudo?
-- =============================================================================
-- Pergunta de negócio: "posso confiar no schema nw como fonte das análises?"
-- Resposta: só se toda linha e todo centavo do original tiverem chegado lá.
-- Este script compara os dois schemas lado a lado. Qualquer linha com
-- divergencia <> 0 ou "DIVERGE" é motivo para parar e investigar.
--
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/21_validacao_carga.sql
-- =============================================================================

\echo
\echo === 1. Contagem de linhas: origem vs destino ===
\echo '(o total e 3311, nao os 3362 do docs/01: a diferenca sao as 51 linhas de'
\echo ' us_states, tabela que ficou fora do modelo por decisao declarada)'
SELECT tabela, origem, destino, destino - origem AS divergencia
FROM (
    SELECT 'regions'              AS tabela, (SELECT count(*) FROM public.region)               AS origem, (SELECT count(*) FROM nw.regions)              AS destino
    UNION ALL SELECT 'territories',          (SELECT count(*) FROM public.territories),                   (SELECT count(*) FROM nw.territories)
    UNION ALL SELECT 'categories',           (SELECT count(*) FROM public.categories),                    (SELECT count(*) FROM nw.categories)
    UNION ALL SELECT 'suppliers',            (SELECT count(*) FROM public.suppliers),                     (SELECT count(*) FROM nw.suppliers)
    UNION ALL SELECT 'shippers',             (SELECT count(*) FROM public.shippers),                      (SELECT count(*) FROM nw.shippers)
    UNION ALL SELECT 'customers',            (SELECT count(*) FROM public.customers),                     (SELECT count(*) FROM nw.customers)
    UNION ALL SELECT 'employees',            (SELECT count(*) FROM public.employees),                     (SELECT count(*) FROM nw.employees)
    UNION ALL SELECT 'employee_territories', (SELECT count(*) FROM public.employee_territories),          (SELECT count(*) FROM nw.employee_territories)
    UNION ALL SELECT 'products',             (SELECT count(*) FROM public.products),                      (SELECT count(*) FROM nw.products)
    UNION ALL SELECT 'orders',               (SELECT count(*) FROM public.orders),                        (SELECT count(*) FROM nw.orders)
    UNION ALL SELECT 'order_items',          (SELECT count(*) FROM public.order_details),                 (SELECT count(*) FROM nw.order_items)
) t
UNION ALL
SELECT 'TOTAL', sum(origem), sum(destino), sum(destino - origem) FROM (
    SELECT (SELECT count(*) FROM public.region) AS origem, (SELECT count(*) FROM nw.regions) AS destino
    UNION ALL SELECT (SELECT count(*) FROM public.territories),          (SELECT count(*) FROM nw.territories)
    UNION ALL SELECT (SELECT count(*) FROM public.categories),           (SELECT count(*) FROM nw.categories)
    UNION ALL SELECT (SELECT count(*) FROM public.suppliers),            (SELECT count(*) FROM nw.suppliers)
    UNION ALL SELECT (SELECT count(*) FROM public.shippers),             (SELECT count(*) FROM nw.shippers)
    UNION ALL SELECT (SELECT count(*) FROM public.customers),            (SELECT count(*) FROM nw.customers)
    UNION ALL SELECT (SELECT count(*) FROM public.employees),            (SELECT count(*) FROM nw.employees)
    UNION ALL SELECT (SELECT count(*) FROM public.employee_territories), (SELECT count(*) FROM nw.employee_territories)
    UNION ALL SELECT (SELECT count(*) FROM public.products),             (SELECT count(*) FROM nw.products)
    UNION ALL SELECT (SELECT count(*) FROM public.orders),               (SELECT count(*) FROM nw.orders)
    UNION ALL SELECT (SELECT count(*) FROM public.order_details),        (SELECT count(*) FROM nw.order_items)
) s;

\echo
\echo === 2. O dinheiro: receita total nos dois schemas ===
\echo '(a diferenca NAO e erro de carga: e o erro de arredondamento do real, que o numeric elimina)'
SELECT
    (SELECT sum(unit_price * quantity * (1 - discount))
       FROM public.order_details)                     AS receita_origem_real,
    (SELECT sum(unit_price * quantity * (1 - discount))
       FROM nw.order_items)                           AS receita_destino_numeric,
    (SELECT sum(unit_price::numeric(10,2) * quantity * (1 - discount::numeric(4,3)))
       FROM public.order_details)                     AS origem_convertida_numeric;

\echo
\echo === 3. Somas de controle por coluna monetaria ===
SELECT coluna, origem, destino, destino - origem AS divergencia FROM (
    SELECT 'orders.freight' AS coluna,
           (SELECT sum(freight::numeric(10,2)) FROM public.orders) AS origem,
           (SELECT sum(freight)                FROM nw.orders)     AS destino
    UNION ALL
    SELECT 'products.unit_price',
           (SELECT sum(unit_price::numeric(10,2)) FROM public.products),
           (SELECT sum(unit_price)                FROM nw.products)
    UNION ALL
    SELECT 'order_items.unit_price',
           (SELECT sum(unit_price::numeric(10,2)) FROM public.order_details),
           (SELECT sum(unit_price)                FROM nw.order_items)
    UNION ALL
    SELECT 'order_items.quantity',
           (SELECT sum(quantity) FROM public.order_details),
           (SELECT sum(quantity) FROM nw.order_items)
) t;

\echo
\echo === 4. As conversoes de tipo preservaram o significado? ===
SELECT 'discontinued: 1 na origem = true no destino' AS verificacao,
       (SELECT count(*) FROM public.products WHERE discontinued = 1) AS origem,
       (SELECT count(*) FROM nw.products     WHERE discontinued)     AS destino
UNION ALL
SELECT 'shipped_date nulo (pedidos nao enviados)',
       (SELECT count(*) FROM public.orders WHERE shipped_date IS NULL),
       (SELECT count(*) FROM nw.orders     WHERE shipped_date IS NULL)
UNION ALL
SELECT 'reports_to nulo (topo da hierarquia)',
       (SELECT count(*) FROM public.employees WHERE reports_to IS NULL),
       (SELECT count(*) FROM nw.employees     WHERE reports_to IS NULL)
UNION ALL
SELECT 'faixa de datas identica (dias entre 1o e ultimo pedido)',
       (SELECT max(order_date) - min(order_date) FROM public.orders),
       (SELECT max(order_date) - min(order_date) FROM nw.orders);

\echo
\echo === 5. Nenhuma chave se perdeu no caminho (anti-join nos dois sentidos) ===
SELECT 'pedidos na origem sem correspondente no nw' AS verificacao,
       count(*) AS linhas
  FROM public.orders o WHERE NOT EXISTS (SELECT 1 FROM nw.orders n WHERE n.order_id = o.order_id)
UNION ALL
SELECT 'itens na origem sem correspondente no nw', count(*)
  FROM public.order_details d
 WHERE NOT EXISTS (SELECT 1 FROM nw.order_items i
                    WHERE i.order_id = d.order_id AND i.product_id = d.product_id)
UNION ALL
SELECT 'clientes na origem sem correspondente no nw', count(*)
  FROM public.customers c WHERE NOT EXISTS (SELECT 1 FROM nw.customers n WHERE n.customer_id = btrim(c.customer_id));

\echo
\echo === 6. O que o schema nw ganhou em regras de negocio ===
\echo '(PK e FK caem de 14/13 para 11/11 porque 3 tabelas ficaram fora do modelo:'
\echo ' as 2 FKs a menos sao as de customer_customer_demo, que esta vazia.'
\echo ' O ganho esta nas linhas CHECK, de 0 para 17, e UNIQUE, de 0 para 4.)'
SELECT tipo,
       count(*) FILTER (WHERE schema = 'public') AS public_origem,
       count(*) FILTER (WHERE schema = 'nw')     AS nw_projeto
FROM (
    SELECT n.nspname AS schema,
           CASE c.contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
                          WHEN 'u' THEN 'UNIQUE'      WHEN 'c' THEN 'CHECK' END AS tipo
      FROM pg_constraint c
      JOIN pg_class      t ON t.oid = c.conrelid
      JOIN pg_namespace  n ON n.oid = t.relnamespace
     WHERE n.nspname IN ('public','nw') AND c.contype IN ('p','f','u','c')
) x
GROUP BY tipo ORDER BY tipo;

\echo
\echo === 7. Colunas que deixaram de aceitar nulo ===
-- O join precisa desfazer os renomes dos DOIS lados: de tabela e de coluna.
-- Sem o renome de coluna, orders.shipper_id (que era ship_via) escapa da conta.
SELECT count(*) AS colunas_agora_obrigatorias
  FROM information_schema.columns nw
  JOIN information_schema.columns pub
    ON pub.table_schema = 'public'
   AND pub.column_name  = CASE nw.column_name
                              WHEN 'shipper_id'     THEN 'ship_via'
                              WHEN 'region_name'    THEN 'region_description'
                              WHEN 'territory_name' THEN 'territory_description'
                              ELSE nw.column_name END
   AND pub.table_name   = CASE nw.table_name WHEN 'regions' THEN 'region'
                                             WHEN 'order_items' THEN 'order_details'
                                             ELSE nw.table_name END
 WHERE nw.table_schema = 'nw'
   AND nw.is_nullable = 'NO' AND pub.is_nullable = 'YES';

\echo
\echo === 8. Nenhuma coluna se perdeu sem declaracao ===
\echo '(a carga descarta 3 colunas de proposito, listadas no cabecalho de 20_load.sql.'
\echo ' Qualquer outra coluna da origem sem correspondente no nw e PERDA SILENCIOSA.)'
SELECT pub.table_name || '.' || pub.column_name AS coluna_da_origem,
       CASE WHEN pub.table_name || '.' || pub.column_name IN (
                'categories.picture', 'employees.photo', 'employees.photo_path')
            THEN 'descartada por decisao (declarada)'
            ELSE '*** PERDA SILENCIOSA ***' END AS situacao
  FROM information_schema.columns pub
 WHERE pub.table_schema = 'public'
   AND pub.table_name NOT IN ('us_states','customer_demographics','customer_customer_demo')
   AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns nw
         WHERE nw.table_schema = 'nw'
           AND nw.table_name   = CASE pub.table_name WHEN 'region' THEN 'regions'
                                                     WHEN 'order_details' THEN 'order_items'
                                                     ELSE pub.table_name END
           AND nw.column_name  = CASE pub.column_name
                                     WHEN 'ship_via'              THEN 'shipper_id'
                                     WHEN 'region_description'    THEN 'region_name'
                                     WHEN 'territory_description' THEN 'territory_name'
                                     ELSE pub.column_name END)
 ORDER BY 2 DESC, 1;

\echo
\echo === 9. O schema opera? (as chaves sinteticas geram valor) ===
\echo '(carregar nao basta: um modelo que nao aceita uma venda nova nao e um modelo)'
SELECT c.relname AS tabela,
       s.last_value AS sequence_no_maior_id_usado,
       CASE WHEN a.attidentity = 'd' THEN 'GENERATED BY DEFAULT' ELSE '*** SEM IDENTITY ***' END AS geracao
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND a.attidentity <> ''
  JOIN pg_sequences s ON s.schemaname = 'nw'
   AND s.sequencename = c.relname || '_' || a.attname || '_seq'
 WHERE n.nspname = 'nw'
 ORDER BY c.relname;
