-- ===========================================================================
-- sql/01_exploracao.sql — Análise exploratória do Northwind original (public)
--
-- O que faz: mede o negócio contido na base — volume financeiro, período,
-- concentração, buracos e anomalias — para embasar docs/01-analise-negocio.md.
--
-- Como rodar:
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/01_exploracao.sql
--
-- Regra do projeto: nenhum número do relatório é estimado. Todos saem daqui.
-- ===========================================================================

\pset footer off

\echo '=== 1. PERÍODO COBERTO E VOLUME DE PEDIDOS ==============================='
SELECT min(order_date)                                   AS primeiro_pedido,
       max(order_date)                                   AS ultimo_pedido,
       (max(order_date) - min(order_date))               AS dias_de_operacao,
       count(*)                                          AS pedidos,
       count(DISTINCT customer_id)                       AS clientes_compradores,
       count(DISTINCT employee_id)                       AS vendedores_ativos
FROM orders;

\echo ''
\echo '=== 2. PEDIDOS POR ANO ==================================================='
SELECT extract(year FROM order_date)::int AS ano,
       count(*)                           AS pedidos,
       count(DISTINCT customer_id)        AS clientes_distintos,
       round(sum(od.receita)::numeric, 2) AS receita
FROM orders o
JOIN LATERAL (
  SELECT sum(unit_price::numeric * quantity * (1 - discount::numeric)) AS receita
  FROM order_details WHERE order_id = o.order_id
) od ON true
GROUP BY 1 ORDER BY 1;

\echo ''
\echo '=== 3. O PROBLEMA DO TIPO real: MESMA CONTA, DOIS RESULTADOS ============='
-- unit_price, discount e freight são `real` (ponto flutuante de 4 bytes).
-- Dinheiro em ponto flutuante acumula erro. Abaixo, a MESMA soma feita nos
-- dois tipos. A diferença é pequena aqui, mas existe e cresce com o volume.
SELECT sum(unit_price * quantity * (1 - discount))                              AS receita_em_real,
       sum(unit_price::numeric * quantity * (1 - discount::numeric))            AS receita_em_numeric,
       sum(unit_price * quantity * (1 - discount))::numeric
         - sum(unit_price::numeric * quantity * (1 - discount::numeric))        AS diferenca
FROM order_details;

\echo ''
\echo '=== 4. TICKET MÉDIO E DISPERSÃO =========================================='
WITH por_pedido AS (
  SELECT o.order_id,
         sum(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric)) AS valor
  FROM orders o JOIN order_details od ON od.order_id = o.order_id
  GROUP BY o.order_id
)
SELECT count(*)                                                AS pedidos_com_item,
       round(min(valor), 2)                                    AS menor,
       round(percentile_cont(0.5) WITHIN GROUP (ORDER BY valor)::numeric, 2) AS mediana,
       round(avg(valor), 2)                                    AS ticket_medio,
       round(percentile_cont(0.95) WITHIN GROUP (ORDER BY valor)::numeric, 2) AS p95,
       round(max(valor), 2)                                    AS maior,
       round(sum(valor), 2)                                    AS receita_total
FROM por_pedido;

\echo ''
\echo '=== 5. ITENS POR PEDIDO =================================================='
SELECT min(itens) AS min_itens, round(avg(itens), 2) AS media_itens, max(itens) AS max_itens
FROM (SELECT order_id, count(*) AS itens FROM order_details GROUP BY order_id) t;

\echo ''
\echo '=== 6. RECEITA POR CATEGORIA (concentração) =============================='
SELECT c.category_name AS categoria,
       count(DISTINCT p.product_id) AS produtos,
       round(sum(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric)), 2) AS receita,
       round(100 * sum(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric))
             / sum(sum(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric))) OVER (), 1) AS pct
FROM order_details od
JOIN products p   ON p.product_id  = od.product_id
JOIN categories c ON c.category_id = p.category_id
GROUP BY c.category_name ORDER BY receita DESC;

\echo ''
\echo '=== 7. RECEITA POR PAÍS DO CLIENTE (top 10) =============================='
SELECT cu.country AS pais,
       count(DISTINCT o.order_id) AS pedidos,
       round(sum(od.unit_price::numeric * od.quantity * (1 - od.discount::numeric)), 2) AS receita
FROM orders o
JOIN customers cu     ON cu.customer_id = o.customer_id
JOIN order_details od ON od.order_id    = o.order_id
GROUP BY cu.country ORDER BY receita DESC LIMIT 10;

\echo ''
\echo '=== 8. ANTI-JOINS: O QUE EXISTE NO CADASTRO MAS NUNCA APARECEU NA VENDA =='
SELECT 'produtos nunca vendidos' AS o_que, count(*) AS quantos FROM products p
  WHERE NOT EXISTS (SELECT 1 FROM order_details od WHERE od.product_id = p.product_id)
UNION ALL
SELECT 'clientes que nunca compraram', count(*) FROM customers c
  WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
UNION ALL
SELECT 'transportadoras nunca usadas', count(*) FROM shippers s
  WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.ship_via = s.shipper_id)
UNION ALL
SELECT 'territórios sem funcionário', count(*) FROM territories t
  WHERE NOT EXISTS (SELECT 1 FROM employee_territories et WHERE et.territory_id = t.territory_id)
UNION ALL
SELECT 'fornecedores sem produto vendido', count(*) FROM suppliers su
  WHERE NOT EXISTS (SELECT 1 FROM products p JOIN order_details od ON od.product_id = p.product_id
                    WHERE p.supplier_id = su.supplier_id)
UNION ALL
SELECT 'pedidos sem nenhum item', count(*) FROM orders o
  WHERE NOT EXISTS (SELECT 1 FROM order_details od WHERE od.order_id = o.order_id);

\echo ''
\echo '--- quem são os clientes que nunca compraram ---'
SELECT c.customer_id, c.company_name, c.country FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
ORDER BY 1;

\echo ''
\echo '--- quais transportadoras nunca foram usadas ---'
SELECT s.shipper_id, s.company_name FROM shippers s
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.ship_via = s.shipper_id)
ORDER BY 1;

\echo ''
\echo '=== 9. O N:N QUE NÃO É N:N: employee_territories ========================='
-- A tabela associativa sugere N:N (um território atendido por vários
-- funcionários). Os dados dizem outra coisa.
SELECT count(*)                        AS vinculos,
       count(DISTINCT employee_id)     AS funcionarios_com_territorio,
       count(DISTINCT territory_id)    AS territorios_vinculados,
       max(func_por_territorio)        AS max_funcionarios_por_territorio
FROM employee_territories,
     LATERAL (SELECT count(*) AS func_por_territorio FROM employee_territories et2
              WHERE et2.territory_id = employee_territories.territory_id) x;

\echo ''
\echo '=== 10. HIERARQUIA DE FUNCIONÁRIOS (auto-relacionamento) ================='
SELECT e.employee_id, e.first_name || ' ' || e.last_name AS funcionario, e.title,
       coalesce(m.first_name || ' ' || m.last_name, '(ninguém — topo)') AS reporta_a,
       (SELECT count(*) FROM employees s WHERE s.reports_to = e.employee_id) AS subordinados
FROM employees e LEFT JOIN employees m ON m.employee_id = e.reports_to
ORDER BY e.employee_id;

\echo ''
\echo '=== 11. DESCONTO: QUAIS VALORES EXISTEM DE FATO =========================='
SELECT round(discount::numeric, 2) AS desconto,
       count(*)                    AS itens,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM order_details GROUP BY 1 ORDER BY 1;

\echo ''
\echo '=== 12. REDUNDÂNCIA INTENCIONAL: preço do catálogo vs preço da venda ====='
-- order_details.unit_price repete products.unit_price. NÃO é erro: é snapshot
-- histórico. A prova é que os dois divergem — o catálogo mudou depois da venda.
SELECT count(*)                                                   AS itens_totais,
       count(*) FILTER (WHERE od.unit_price <> p.unit_price)      AS itens_com_preco_diferente,
       round(100.0 * count(*) FILTER (WHERE od.unit_price <> p.unit_price) / count(*), 1) AS pct_divergente
FROM order_details od JOIN products p ON p.product_id = od.product_id;

\echo ''
\echo '--- exemplo concreto da divergência (5 casos) ---'
SELECT p.product_name AS produto,
       p.unit_price   AS preco_catalogo_hoje,
       od.unit_price  AS preco_cobrado_na_venda,
       o.order_date   AS data_da_venda
FROM order_details od
JOIN products p ON p.product_id = od.product_id
JOIN orders   o ON o.order_id   = od.order_id
WHERE od.unit_price <> p.unit_price
ORDER BY p.product_name, o.order_date LIMIT 5;

\echo ''
\echo '=== 13. QUALIDADE DA ENTREGA ============================================='
SELECT count(*)                                                      AS pedidos,
       count(*) FILTER (WHERE shipped_date IS NULL)                  AS nunca_enviados,
       count(*) FILTER (WHERE shipped_date > required_date)          AS enviados_com_atraso,
       round(avg(shipped_date - order_date) FILTER (WHERE shipped_date IS NOT NULL), 1) AS dias_medios_ate_envio
FROM orders;

\echo ''
\echo '=== 14. REDUNDÂNCIA ACIDENTAL: endereço de entrega solto em orders ======='
-- orders guarda ship_name/address/city/region/postal_code/country em colunas
-- soltas. Quanto disso é simples cópia do cadastro do cliente?
-- O numero depende de quantas colunas se compara, e a diferenca importa: o
-- criterio de tres colunas mede "o endereco postal"; o de seis mede "o
-- endereco inteiro", incluindo destinatario, regiao e CEP.
SELECT count(*)                                                       AS pedidos_com_cliente,
       count(*) FILTER (WHERE o.ship_name = c.company_name)           AS ship_name_igual_ao_cliente,
       count(*) FILTER (WHERE o.ship_address = c.address
                          AND o.ship_city = c.city
                          AND o.ship_country = c.country)             AS iguais_por_3_colunas,
       count(*) FILTER (WHERE o.ship_address = c.address
                          AND o.ship_city = c.city
                          AND o.ship_country = c.country
                          AND o.ship_region      IS NOT DISTINCT FROM c.region
                          AND o.ship_postal_code IS NOT DISTINCT FROM c.postal_code
                          AND o.ship_name        = c.company_name)    AS iguais_por_6_colunas,
       count(*) - count(*) FILTER (WHERE o.ship_address = c.address
                          AND o.ship_city = c.city
                          AND o.ship_country = c.country)             AS diferentes_por_3_colunas,
       count(*) - count(*) FILTER (WHERE o.ship_address = c.address
                          AND o.ship_city = c.city
                          AND o.ship_country = c.country
                          AND o.ship_region      IS NOT DISTINCT FROM c.region
                          AND o.ship_postal_code IS NOT DISTINCT FROM c.postal_code
                          AND o.ship_name        = c.company_name)    AS diferentes_por_6_colunas
FROM orders o JOIN customers c ON c.customer_id = o.customer_id;

\echo ''
\echo '=== 15. TABELAS ÓRFÃS E VAZIAS =========================================='
SELECT 'customer_demographics'  AS tabela, count(*) AS linhas, 'sem uso; descreve segmento de cliente' AS observacao FROM customer_demographics
UNION ALL SELECT 'customer_customer_demo', count(*), 'associativa vazia (N:N sem dados)' FROM customer_customer_demo
UNION ALL SELECT 'us_states', count(*), 'preenchida, mas SEM nenhuma FK apontando para ela' FROM us_states
ORDER BY 1;

\echo ''
\echo '=== 16. LIMITE DO TIPO smallint EM order_id ============================='
-- order_id é smallint: o teto é 32767. Qual a folga real?
SELECT min(order_id) AS menor_id, max(order_id) AS maior_id,
       32767 AS teto_do_smallint,
       32767 - max(order_id) AS folga_ate_estourar
FROM orders;

\echo ''
\echo '=== 17. FAIXAS DE VALOR (base para os CHECK do schema nw) ==============='
SELECT 'order_details.unit_price' AS coluna, min(unit_price)::numeric AS minimo, max(unit_price)::numeric AS maximo, count(*) FILTER (WHERE unit_price < 0) AS violacoes_da_faixa_proposta FROM order_details
UNION ALL SELECT 'order_details.quantity', min(quantity), max(quantity), count(*) FILTER (WHERE quantity <= 0) FROM order_details
UNION ALL SELECT 'order_details.discount', min(discount)::numeric, max(discount)::numeric, count(*) FILTER (WHERE discount < 0 OR discount >= 1) FROM order_details
UNION ALL SELECT 'orders.freight', min(freight)::numeric, max(freight)::numeric, count(*) FILTER (WHERE freight < 0) FROM orders
UNION ALL SELECT 'products.unit_price', min(unit_price)::numeric, max(unit_price)::numeric, count(*) FILTER (WHERE unit_price < 0) FROM products
UNION ALL SELECT 'products.units_in_stock', min(units_in_stock), max(units_in_stock), count(*) FILTER (WHERE units_in_stock < 0) FROM products
UNION ALL SELECT 'products.discontinued', min(discontinued), max(discontinued), count(*) FILTER (WHERE discontinued NOT IN (0,1)) FROM products;

\echo ''
\echo '--- coerência temporal: alguma data fora de ordem? ---'
SELECT count(*) FILTER (WHERE shipped_date < order_date)  AS enviado_antes_de_pedido,
       count(*) FILTER (WHERE required_date < order_date) AS prazo_anterior_ao_pedido,
       count(*) FILTER (WHERE order_date IS NULL)         AS pedido_sem_data
FROM orders;

\echo ''
\echo '--- descontos fora da escala comercial de 5 em 5 pontos ---'
SELECT round(discount::numeric,2) AS desconto, count(*) AS itens
FROM order_details
WHERE discount > 0 AND (discount::numeric * 100)::int % 5 <> 0
GROUP BY 1 ORDER BY 1;

\echo ''
\echo '=== 18. NULO POR INAPLICABILIDADE: prova em employees.region ============'
-- 4 dos 9 funcionarios tem region NULL. Nao e dado faltando: sao os 4 do
-- escritorio de Londres, e "region/estado" nao se aplica a um endereco no
-- Reino Unido. Distinguir isso de dado ausente muda a decisao de modelagem.
SELECT country,
       count(*)                                AS funcionarios,
       count(region)                           AS com_region_preenchida,
       count(*) - count(region)                AS com_region_nula,
       string_agg(DISTINCT city, ', ' ORDER BY city) AS cidades
FROM employees GROUP BY country ORDER BY country;

\echo ''
\echo '--- us_states: quantas FKs apontam para ela? (esperado: 0 = tabela ilha) ---'
SELECT count(*) AS fks_apontando_para_us_states
FROM pg_constraint WHERE contype='f' AND confrelid='public.us_states'::regclass;
