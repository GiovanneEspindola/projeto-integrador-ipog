-- Tutorial prático da Entrega 1. Cada bloco é uma consulta independente.
-- Abra no DBeaver e execute o bloco selecionado com Ctrl+Enter.
-- Só SELECT: não carrega, altera ou apaga dados.
-- 00 a 21: fonte public; 22: comparação com nw; 23 a 25: planejamento;
-- 26 a 30: exportações sem agregação para recalcular em Python.
-- As explicações estão em docs/estudo/tutorial-entrega01-dbeaver.md.

-- @00 Conexão e contexto
SELECT current_database() AS banco, current_user AS usuario, current_schema() AS schema_atual, current_setting('server_version') AS versao, current_setting('transaction_read_only') AS somente_leitura;

-- @01 Inventário exato das 14 tabelas
WITH contagens AS (
SELECT 'categories' AS tabela, count(*) AS linhas FROM public.categories
UNION ALL
SELECT 'customer_customer_demo' AS tabela, count(*) AS linhas FROM public.customer_customer_demo
UNION ALL
SELECT 'customer_demographics' AS tabela, count(*) AS linhas FROM public.customer_demographics
UNION ALL
SELECT 'customers' AS tabela, count(*) AS linhas FROM public.customers
UNION ALL
SELECT 'employees' AS tabela, count(*) AS linhas FROM public.employees
UNION ALL
SELECT 'employee_territories' AS tabela, count(*) AS linhas FROM public.employee_territories
UNION ALL
SELECT 'order_details' AS tabela, count(*) AS linhas FROM public.order_details
UNION ALL
SELECT 'orders' AS tabela, count(*) AS linhas FROM public.orders
UNION ALL
SELECT 'products' AS tabela, count(*) AS linhas FROM public.products
UNION ALL
SELECT 'region' AS tabela, count(*) AS linhas FROM public.region
UNION ALL
SELECT 'shippers' AS tabela, count(*) AS linhas FROM public.shippers
UNION ALL
SELECT 'suppliers' AS tabela, count(*) AS linhas FROM public.suppliers
UNION ALL
SELECT 'territories' AS tabela, count(*) AS linhas FROM public.territories
UNION ALL
SELECT 'us_states' AS tabela, count(*) AS linhas FROM public.us_states
)
SELECT tabela, linhas FROM contagens
UNION ALL SELECT 'TOTAL', sum(linhas) FROM contagens
ORDER BY tabela;

-- @02 Colunas e tipos da fonte
SELECT table_name AS tabela, column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo
FROM information_schema.columns
WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;

-- @03 Entender um pedido concreto
SELECT o.order_id, o.customer_id, c.company_name, o.order_date,
       o.required_date, o.shipped_date, o.freight
FROM public.orders o JOIN public.customers c USING (customer_id)
WHERE o.order_id = 10248;

-- @04 Calcular os três itens do pedido 10248
SELECT d.product_id, p.product_name, d.unit_price::numeric AS preco,
       d.quantity, d.discount::numeric AS desconto,
       d.unit_price::numeric * d.quantity * (1-d.discount::numeric) AS valor
FROM public.order_details d
JOIN public.products p USING (product_id)
WHERE d.order_id = 10248 ORDER BY d.product_id;

-- @05 Período e volume
SELECT min(order_date) AS primeiro_pedido,
       max(order_date) AS ultimo_pedido,
       count(*) AS pedidos,
       count(DISTINCT customer_id) AS clientes_com_pedido
FROM public.orders;

-- @06 Total, média e mediana
WITH totais AS (
  SELECT order_id,
         sum(unit_price::numeric * quantity *
             (1 - discount::numeric)) AS valor
  FROM public.order_details GROUP BY order_id
)
SELECT round(sum(valor), 2) AS total,
       round(avg(valor), 2) AS media,
       round(percentile_cont(0.5) WITHIN GROUP
             (ORDER BY valor)::numeric, 2) AS mediana,
       round(min(valor), 2) AS minimo,
       round(max(valor), 2) AS maximo
FROM totais;

-- @07 Pedidos e valores por ano
SELECT extract(year FROM o.order_date)::int AS ano,
       count(DISTINCT o.order_id) AS pedidos,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.orders o
JOIN public.order_details d ON d.order_id = o.order_id
GROUP BY 1 ORDER BY 1;

-- @08 Categorias e concentração
SELECT c.category_name AS categoria,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id
JOIN public.categories c ON c.category_id = p.category_id
GROUP BY c.category_name ORDER BY valor DESC;

-- @09 Nulos em todas as colunas preenchidas da fonte
WITH registros AS (
SELECT 'categories' AS tabela, to_jsonb(t) AS registro FROM public.categories t
UNION ALL
SELECT 'customer_customer_demo' AS tabela, to_jsonb(t) AS registro FROM public.customer_customer_demo t
UNION ALL
SELECT 'customer_demographics' AS tabela, to_jsonb(t) AS registro FROM public.customer_demographics t
UNION ALL
SELECT 'customers' AS tabela, to_jsonb(t) AS registro FROM public.customers t
UNION ALL
SELECT 'employees' AS tabela, to_jsonb(t) AS registro FROM public.employees t
UNION ALL
SELECT 'employee_territories' AS tabela, to_jsonb(t) AS registro FROM public.employee_territories t
UNION ALL
SELECT 'order_details' AS tabela, to_jsonb(t) AS registro FROM public.order_details t
UNION ALL
SELECT 'orders' AS tabela, to_jsonb(t) AS registro FROM public.orders t
UNION ALL
SELECT 'products' AS tabela, to_jsonb(t) AS registro FROM public.products t
UNION ALL
SELECT 'region' AS tabela, to_jsonb(t) AS registro FROM public.region t
UNION ALL
SELECT 'shippers' AS tabela, to_jsonb(t) AS registro FROM public.shippers t
UNION ALL
SELECT 'suppliers' AS tabela, to_jsonb(t) AS registro FROM public.suppliers t
UNION ALL
SELECT 'territories' AS tabela, to_jsonb(t) AS registro FROM public.territories t
UNION ALL
SELECT 'us_states' AS tabela, to_jsonb(t) AS registro FROM public.us_states t
), perfil AS (
  SELECT tabela, c.key AS coluna, count(*) AS linhas,
         count(*) FILTER (WHERE c.value = 'null'::jsonb) AS nulos
  FROM registros CROSS JOIN LATERAL jsonb_each(registro) c
  GROUP BY tabela, c.key
)
SELECT tabela, coluna, linhas, nulos,
       round(100.0*nulos/linhas,2) AS percentual
FROM perfil WHERE nulos > 0 ORDER BY tabela,coluna;

-- @10 Data de envio ausente e tempo até o envio
SELECT count(*) AS pedidos,
       count(*) FILTER (WHERE shipped_date IS NULL) AS sem_data,
       round(100.0 * count(*) FILTER
         (WHERE shipped_date IS NULL) / count(*), 2) AS pct_sem_data,
       round(avg(shipped_date - order_date), 2) AS dias_ate_envio
FROM public.orders;

-- @11 Chaves e restrições existentes
SELECT c.conrelid::regclass AS tabela, c.conname AS nome,
       CASE c.contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
         WHEN 'c' THEN 'CHECK' WHEN 'u' THEN 'UNIQUE' END AS tipo,
       pg_get_constraintdef(c.oid) AS definicao
FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
WHERE n.nspname='public' AND c.contype IN ('p','f','c','u')
ORDER BY tipo,c.conrelid::regclass::text,nome;

-- @12 Órfãos nas 13 relações
SELECT 'orders.customer_id' AS referencia, count(*) AS orfaos
FROM public.orders f WHERE f.customer_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.customers p WHERE p.customer_id=f.customer_id)
UNION ALL
SELECT 'orders.employee_id' AS referencia, count(*) AS orfaos
FROM public.orders f WHERE f.employee_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.employees p WHERE p.employee_id=f.employee_id)
UNION ALL
SELECT 'orders.ship_via' AS referencia, count(*) AS orfaos
FROM public.orders f WHERE f.ship_via IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.shippers p WHERE p.shipper_id=f.ship_via)
UNION ALL
SELECT 'order_details.order_id' AS referencia, count(*) AS orfaos
FROM public.order_details f WHERE f.order_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.orders p WHERE p.order_id=f.order_id)
UNION ALL
SELECT 'order_details.product_id' AS referencia, count(*) AS orfaos
FROM public.order_details f WHERE f.product_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.products p WHERE p.product_id=f.product_id)
UNION ALL
SELECT 'products.category_id' AS referencia, count(*) AS orfaos
FROM public.products f WHERE f.category_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.categories p WHERE p.category_id=f.category_id)
UNION ALL
SELECT 'products.supplier_id' AS referencia, count(*) AS orfaos
FROM public.products f WHERE f.supplier_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.suppliers p WHERE p.supplier_id=f.supplier_id)
UNION ALL
SELECT 'territories.region_id' AS referencia, count(*) AS orfaos
FROM public.territories f WHERE f.region_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.region p WHERE p.region_id=f.region_id)
UNION ALL
SELECT 'employee_territories.territory_id' AS referencia, count(*) AS orfaos
FROM public.employee_territories f WHERE f.territory_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.territories p WHERE p.territory_id=f.territory_id)
UNION ALL
SELECT 'employee_territories.employee_id' AS referencia, count(*) AS orfaos
FROM public.employee_territories f WHERE f.employee_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.employees p WHERE p.employee_id=f.employee_id)
UNION ALL
SELECT 'customer_customer_demo.customer_type_id' AS referencia, count(*) AS orfaos
FROM public.customer_customer_demo f WHERE f.customer_type_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.customer_demographics p WHERE p.customer_type_id=f.customer_type_id)
UNION ALL
SELECT 'customer_customer_demo.customer_id' AS referencia, count(*) AS orfaos
FROM public.customer_customer_demo f WHERE f.customer_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.customers p WHERE p.customer_id=f.customer_id)
UNION ALL
SELECT 'employees.reports_to' AS referencia, count(*) AS orfaos
FROM public.employees f WHERE f.reports_to IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM public.employees p WHERE p.employee_id=f.reports_to);

-- @13 Duplicidades pelas chaves das 14 tabelas
SELECT 'categories' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT category_id FROM public.categories
      GROUP BY category_id HAVING count(*) > 1) d
UNION ALL
SELECT 'customer_customer_demo' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT customer_id,customer_type_id FROM public.customer_customer_demo
      GROUP BY customer_id,customer_type_id HAVING count(*) > 1) d
UNION ALL
SELECT 'customer_demographics' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT customer_type_id FROM public.customer_demographics
      GROUP BY customer_type_id HAVING count(*) > 1) d
UNION ALL
SELECT 'customers' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT customer_id FROM public.customers
      GROUP BY customer_id HAVING count(*) > 1) d
UNION ALL
SELECT 'employees' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT employee_id FROM public.employees
      GROUP BY employee_id HAVING count(*) > 1) d
UNION ALL
SELECT 'employee_territories' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT employee_id,territory_id FROM public.employee_territories
      GROUP BY employee_id,territory_id HAVING count(*) > 1) d
UNION ALL
SELECT 'order_details' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT order_id,product_id FROM public.order_details
      GROUP BY order_id,product_id HAVING count(*) > 1) d
UNION ALL
SELECT 'orders' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT order_id FROM public.orders
      GROUP BY order_id HAVING count(*) > 1) d
UNION ALL
SELECT 'products' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT product_id FROM public.products
      GROUP BY product_id HAVING count(*) > 1) d
UNION ALL
SELECT 'region' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT region_id FROM public.region
      GROUP BY region_id HAVING count(*) > 1) d
UNION ALL
SELECT 'shippers' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT shipper_id FROM public.shippers
      GROUP BY shipper_id HAVING count(*) > 1) d
UNION ALL
SELECT 'suppliers' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT supplier_id FROM public.suppliers
      GROUP BY supplier_id HAVING count(*) > 1) d
UNION ALL
SELECT 'territories' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT territory_id FROM public.territories
      GROUP BY territory_id HAVING count(*) > 1) d
UNION ALL
SELECT 'us_states' AS tabela, count(*) AS grupos_duplicados
FROM (SELECT state_id FROM public.us_states
      GROUP BY state_id HAVING count(*) > 1) d;

-- @14 Faixas e coerência temporal
SELECT 'quantidade <= 0' AS verificacao, count(*) AS casos
FROM public.order_details WHERE quantity <= 0
UNION ALL
SELECT 'preço < 0', count(*) FROM public.order_details WHERE unit_price < 0
UNION ALL
SELECT 'desconto fora de [0, 1)', count(*)
FROM public.order_details WHERE discount < 0 OR discount >= 1
UNION ALL
SELECT 'envio anterior ao pedido', count(*)
FROM public.orders WHERE shipped_date < order_date
UNION ALL
SELECT 'prazo anterior ao pedido', count(*) FROM public.orders WHERE required_date < order_date
UNION ALL
SELECT 'pedido sem data', count(*) FROM public.orders WHERE order_date IS NULL
UNION ALL
SELECT 'frete negativo', count(*) FROM public.orders WHERE freight < 0
UNION ALL
SELECT 'estoque negativo', count(*) FROM public.products WHERE units_in_stock < 0
UNION ALL
SELECT 'discontinued fora de 0/1', count(*) FROM public.products WHERE discontinued NOT IN (0,1);

-- @15 Faixas observadas, sem presumir limites do negócio
SELECT min(unit_price)::numeric AS menor_preco, max(unit_price)::numeric AS maior_preco,
       min(quantity) AS menor_quantidade, max(quantity) AS maior_quantidade,
       min(discount)::numeric AS menor_desconto, max(discount)::numeric AS maior_desconto
FROM public.order_details;

-- @16 Pedidos vazios e cadastros sem movimento
SELECT 'pedidos sem item' AS indicador,count(*) AS quantidade
FROM public.orders o WHERE NOT EXISTS(SELECT 1 FROM public.order_details d WHERE d.order_id=o.order_id)
UNION ALL SELECT 'clientes sem pedido',count(*) FROM public.customers c WHERE NOT EXISTS(SELECT 1 FROM public.orders o WHERE o.customer_id=c.customer_id)
UNION ALL SELECT 'produtos sem venda',count(*) FROM public.products p WHERE NOT EXISTS(SELECT 1 FROM public.order_details d WHERE d.product_id=p.product_id)
UNION ALL SELECT 'transportadoras sem pedido',count(*) FROM public.shippers s WHERE NOT EXISTS(SELECT 1 FROM public.orders o WHERE o.ship_via=s.shipper_id)
UNION ALL SELECT 'territórios sem funcionário',count(*) FROM public.territories t WHERE NOT EXISTS(SELECT 1 FROM public.employee_territories e WHERE e.territory_id=t.territory_id);

-- @17 Preço do item e preço do catálogo
SELECT count(*) AS itens,
       count(*) FILTER
         (WHERE d.unit_price <> p.unit_price) AS precos_diferentes
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id;

-- @18 Comparar os seis campos de endereço com nulos correspondentes
SELECT count(*) AS pedidos, count(*) FILTER (WHERE
  ROW(o.ship_name,o.ship_address,o.ship_city,o.ship_region,o.ship_postal_code,o.ship_country)
  IS NOT DISTINCT FROM
  ROW(c.company_name,c.address,c.city,c.region,c.postal_code,c.country)) AS seis_campos_iguais
FROM public.orders o JOIN public.customers c USING(customer_id);

-- @19 Momento do arredondamento
SELECT round(sum(unit_price::numeric * quantity *
                 (1 - discount::numeric)), 2) AS arredondar_total,
       sum(round(unit_price::numeric * quantity *
                 (1 - discount::numeric), 2)) AS arredondar_itens
FROM public.order_details;

-- @20 Cardinalidade observada de atuação
SELECT count(*) AS vinculos, count(DISTINCT employee_id) AS funcionarios,
       count(DISTINCT territory_id) AS territorios,
       (SELECT max(n) FROM (SELECT count(*) n FROM public.employee_territories GROUP BY territory_id) x) AS max_funcionarios_por_territorio
FROM public.employee_territories;

-- @21 Como uma junção muda a contagem
SELECT count(*) AS linhas_apos_join, count(DISTINCT o.order_id) AS pedidos,
       sum(d.quantity) AS unidades
FROM public.orders o JOIN public.order_details d USING(order_id);

-- @22 Comparar todos os valores dos itens migrados nos dois sentidos
WITH origem AS (
  SELECT order_id,product_id,unit_price::numeric(10,2) AS unit_price,
         quantity,discount::numeric(4,3) AS discount FROM public.order_details
), destino AS (
  SELECT order_id,product_id,unit_price,quantity,discount FROM nw.order_items
)
SELECT 'origem sem equivalente' AS sentido,count(*) AS diferencas
FROM (SELECT * FROM origem EXCEPT ALL SELECT * FROM destino) x
UNION ALL
SELECT 'destino sem equivalente',count(*)
FROM (SELECT * FROM destino EXCEPT ALL SELECT * FROM origem) y;

-- @23 Protótipo de documento, exibido sem gravar no MongoDB
SELECT jsonb_pretty(jsonb_build_object(
  '_id',o.order_id,'customer_id',o.customer_id,
  'employee_id',o.employee_id,'shipper_id',o.ship_via,
  'order_date',o.order_date,'shipped_date',o.shipped_date,
  'freight',o.freight::numeric,
  'ship_address',jsonb_build_object('name',o.ship_name,'address',o.ship_address,
    'city',o.ship_city,'region',o.ship_region,'postal_code',o.ship_postal_code,'country',o.ship_country),
  'items',(SELECT jsonb_agg(jsonb_build_object('product_id',d.product_id,
      'category_id',p.category_id,'unit_price',d.unit_price::numeric,
      'quantity',d.quantity,'discount',d.discount::numeric) ORDER BY d.product_id)
    FROM public.order_details d JOIN public.products p USING(product_id)
    WHERE d.order_id=o.order_id)
)) AS exemplo_documento
FROM public.orders o WHERE o.order_id=10248;

-- @24 Conferir quantidade de documentos e itens do agrupamento
WITH documentos AS (
 SELECT o.order_id, (SELECT jsonb_agg(to_jsonb(d) ORDER BY d.product_id)
   FROM public.order_details d WHERE d.order_id=o.order_id) AS itens
 FROM public.orders o
)
SELECT count(*) AS documentos, sum(jsonb_array_length(itens)) AS itens,
       min(jsonb_array_length(itens)) AS menor_array,
       max(jsonb_array_length(itens)) AS maior_array,
       count(*) FILTER (WHERE itens IS NULL) AS sem_itens
FROM documentos;

-- @25 Cadastros que o modelo documental precisa preservar
SELECT s.shipper_id,s.company_name FROM public.shippers s
WHERE NOT EXISTS(SELECT 1 FROM public.orders o WHERE o.ship_via=s.shipper_id)
ORDER BY s.shipper_id;

-- @26 Exportação independente: itens.csv
SELECT order_id,product_id,unit_price::text AS unit_price,quantity,discount::text AS discount
FROM public.order_details ORDER BY order_id,product_id;

-- @27 Exportação independente: pedidos.csv
SELECT order_id,customer_id,employee_id,order_date,shipped_date
FROM public.orders ORDER BY order_id;

-- @28 Exportação independente: produtos.csv
SELECT product_id,product_name,category_id,unit_price::text AS unit_price
FROM public.products ORDER BY product_id;

-- @29 Exportação independente: categorias.csv
SELECT category_id,category_name FROM public.categories ORDER BY category_id;

-- @30 Exportação independente: clientes.csv
SELECT customer_id,company_name FROM public.customers ORDER BY customer_id;
