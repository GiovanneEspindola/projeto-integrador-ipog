-- Consultas selecionadas para o relatório da Entrega 1.
-- Executar em PostgreSQL 16. Todas as consultas são somente leitura.
-- Os marcadores permitem inserir o comando e sua saída juntos no Word.

-- @resumo Período e volume
SELECT min(order_date) AS primeiro_pedido,
       max(order_date) AS ultimo_pedido,
       count(*) AS pedidos,
       count(DISTINCT customer_id) AS clientes_com_pedido
FROM public.orders;

-- @anos Pedidos e valor por ano
SELECT extract(year FROM o.order_date)::int AS ano,
       count(DISTINCT o.order_id) AS pedidos,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.orders o
JOIN public.order_details d ON d.order_id = o.order_id
GROUP BY 1 ORDER BY 1;

-- @valores Distribuição do valor dos pedidos
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

-- @categorias Valor dos pedidos por categoria
SELECT c.category_name AS categoria,
       round(sum(d.unit_price::numeric * d.quantity *
                 (1 - d.discount::numeric)), 2) AS valor
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id
JOIN public.categories c ON c.category_id = p.category_id
GROUP BY c.category_name ORDER BY valor DESC;

-- @envio Ausência de data e intervalo até o envio
SELECT count(*) AS pedidos,
       count(*) FILTER (WHERE shipped_date IS NULL) AS sem_data,
       round(100.0 * count(*) FILTER
         (WHERE shipped_date IS NULL) / count(*), 2) AS pct_sem_data,
       round(avg(shipped_date - order_date), 2) AS dias_ate_envio
FROM public.orders;

-- @integridade Integridade de pedidos e itens
SELECT 'pedido sem cliente válido' AS verificacao, count(*) AS casos
FROM public.orders o WHERE NOT EXISTS (
  SELECT 1 FROM public.customers c WHERE c.customer_id = o.customer_id)
UNION ALL
SELECT 'item sem pedido válido', count(*)
FROM public.order_details d WHERE NOT EXISTS (
  SELECT 1 FROM public.orders o WHERE o.order_id = d.order_id)
UNION ALL
SELECT 'pedido sem item', count(*)
FROM public.orders o WHERE NOT EXISTS (
  SELECT 1 FROM public.order_details d WHERE d.order_id = o.order_id);

-- @dominios Validade de valores e datas
SELECT 'quantidade <= 0' AS verificacao, count(*) AS casos
FROM public.order_details WHERE quantity <= 0
UNION ALL
SELECT 'preço < 0', count(*) FROM public.order_details WHERE unit_price < 0
UNION ALL
SELECT 'desconto fora de [0, 1)', count(*)
FROM public.order_details WHERE discount < 0 OR discount >= 1
UNION ALL
SELECT 'envio anterior ao pedido', count(*)
FROM public.orders WHERE shipped_date < order_date;

-- @precos Preço registrado no item e no catálogo
SELECT count(*) AS itens,
       count(*) FILTER
         (WHERE d.unit_price <> p.unit_price) AS precos_diferentes
FROM public.order_details d
JOIN public.products p ON p.product_id = d.product_id;

-- @arredondamento Efeito do momento do arredondamento
SELECT round(sum(unit_price::numeric * quantity *
                 (1 - discount::numeric)), 2) AS arredondar_total,
       sum(round(unit_price::numeric * quantity *
                 (1 - discount::numeric), 2)) AS arredondar_itens
FROM public.order_details;
