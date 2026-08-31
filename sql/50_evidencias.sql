-- =============================================================================
-- 50_evidencias.sql — prova de que os índices e as views fazem o que dizem
-- =============================================================================
-- Roda os EXPLAIN que justificam cada índice de 30_indexes.sql e os números de
-- controle de cada view de 40_views.sql. A saída deste arquivo é a evidência
-- que vai para a apresentação — nenhum número dos documentos foi digitado à mão.
--
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/50_evidencias.sql
-- =============================================================================

SET search_path TO nw;

\echo
\echo '###############################################################'
\echo '# PARTE 1 — os quatro indices que entraram, e a prova de uso   #'
\echo '###############################################################'
\echo
\echo '--- orders_customer_idx: pedidos de um cliente (6 linhas de 830) ---'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, TIMING OFF, SUMMARY OFF)
SELECT * FROM orders WHERE customer_id = 'ALFKI';
\echo
\echo '--- orders_employee_idx: pedidos de um vendedor (156 de 830) ---'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, TIMING OFF, SUMMARY OFF)
SELECT * FROM orders WHERE employee_id = 4;
\echo
\echo '--- orders_date_idx: pedidos de um mes (33 de 830) — Index Only Scan ---'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, TIMING OFF, SUMMARY OFF)
SELECT count(*) FROM orders WHERE order_date BETWEEN '1997-01-01' AND '1997-01-31';
\echo
\echo '--- order_items_product_idx: vendas de um produto (38 de 2155) ---'
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, TIMING OFF, SUMMARY OFF)
SELECT * FROM order_items WHERE product_id = 11;

\echo
\echo '###############################################################'
\echo '# PARTE 2 — os candidatos recusados, e a medicao que recusou   #'
\echo '###############################################################'
\echo
\echo '--- order_items(order_id) NAO foi criado: a PK composta ja atende ---'
EXPLAIN (COSTS OFF) SELECT * FROM order_items WHERE order_id = 10248;
\echo
\echo '--- products(category_id) NAO foi criado: a tabela tem 1 pagina ---'
EXPLAIN (COSTS OFF) SELECT * FROM products WHERE category_id = 1;
\echo
\echo '--- employee_territories(territory_id) NAO foi criado: 1 pagina ---'
EXPLAIN (COSTS OFF) SELECT * FROM employee_territories WHERE territory_id = '10019';
\echo
\echo '--- products(supplier_id) NAO foi criado: a UNIQUE ja cria um indice que'
\echo '    comeca por supplier_id, e mesmo ele o planejador nao usa (1 pagina) ---'
EXPLAIN (COSTS OFF) SELECT * FROM products WHERE supplier_id = 1;
\echo
\echo '--- territories(region_id) NAO foi criado: 1 pagina ---'
EXPLAIN (COSTS OFF) SELECT * FROM territories WHERE region_id = 1;
\echo
\echo '--- orders(customer_id, order_date) NAO foi criado: tem nicho, mas estreito.'
\echo '    Os tres planos abaixo sao COM o indice composto criado em transacao. ---'
BEGIN;
CREATE INDEX tmp_cust_date ON orders (customer_id, order_date);
ANALYZE orders;
\echo '  (a) cliente com 30 pedidos, LIMIT 5 -> ignora o composto:'
EXPLAIN (COSTS OFF) SELECT order_id, order_date FROM orders
 WHERE customer_id='ERNSH' ORDER BY order_date DESC LIMIT 5;
\echo '  (b) cliente com 6 pedidos, LIMIT 5 -> ignora o composto:'
EXPLAIN (COSTS OFF) SELECT order_id, order_date FROM orders
 WHERE customer_id='ALFKI' ORDER BY order_date DESC LIMIT 5;
\echo '  (c) cliente com 6 pedidos, LIMIT 1 -> AQUI ele usa o composto.'
\echo '      Nenhuma das 16 perguntas tem esta forma, por isso o indice nao entrou:'
EXPLAIN (COSTS OFF) SELECT order_id, order_date FROM orders
 WHERE customer_id='ALFKI' ORDER BY order_date DESC LIMIT 1;
ROLLBACK;
\echo
\echo '--- a PK composta COBRE MAL a busca pela segunda coluna: com o indice'
\echo '    dedicado removido e o Seq Scan desligado, ela e usada mesmo assim ---'
BEGIN;
DROP INDEX order_items_product_idx;
SET enable_seqscan = off;
EXPLAIN (COSTS OFF) SELECT * FROM order_items WHERE product_id = 11;
ROLLBACK;
\echo
\echo '--- indice nao ajuda quando a consulta le TUDO: agregacao usa Seq Scan ---'
EXPLAIN (COSTS OFF)
SELECT categoria, sum(receita) FROM vw_venda_item GROUP BY 1;
\echo
\echo '--- tamanho real das tabelas, que explica quase todas as recusas ---'
SELECT relname AS tabela, reltuples::int AS linhas, relpages AS paginas_8kb
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'nw' AND c.relkind = 'r'
 ORDER BY relpages DESC, relname;

\echo
\echo '###############################################################'
\echo '# PARTE 3 — as quatro views e seus numeros de controle         #'
\echo '###############################################################'
\echo
\echo '--- vw_venda_item: 2155 linhas e a receita total ---'
\echo '(a view arredonda cada item, como faz uma nota fiscal; por isso o total'
\echo ' fica 0,25 acima da soma sem arredondar — e diferenca esperada, nao erro)'
SELECT count(*) AS linhas,
       sum(receita)                                            AS receita_arredondada_por_item,
       (SELECT sum(unit_price*quantity*(1-discount)) FROM order_items) AS receita_sem_arredondar,
       sum(valor_do_desconto)                                  AS desconto_total
  FROM vw_venda_item;

\echo
\echo '--- vw_pedido_resumo: os 830 pedidos ---'
SELECT count(*) AS pedidos, sum(itens) AS itens, sum(valor_pedido) AS valor,
       count(*) FILTER (WHERE dias_para_envio IS NULL) AS nunca_enviados,
       count(*) FILTER (WHERE entregue_com_atraso)     AS entregues_com_atraso,
       round(avg(dias_para_envio), 1)                  AS media_dias_para_envio
  FROM vw_pedido_resumo;

\echo
\echo '--- vw_estoque_critico: produtos abaixo do ponto de reposicao ---'
SELECT produto, categoria, estoque, encomendado, ponto_de_reposicao, cobertura
  FROM vw_estoque_critico ORDER BY folga_apos_chegada, produto;

\echo
\echo '--- vw_hierarquia_funcionarios: a CTE recursiva resolveu a arvore ---'
SELECT employee_id, funcionario, cargo, nivel, chefe
  FROM vw_hierarquia_funcionarios ORDER BY nivel, employee_id;
