-- Q11 — RFM descritivo dos clientes
-- Pergunta: Qual é o perfil de recência, frequência e valor de cada cliente?
-- Resultado: Recência (dias), frequência (pedidos) e valor de cada cliente, com escores 0 a 3 em faixas fixas.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH rfm AS (
 SELECT c.customer_id,DATE '1998-05-06'-max(o.order_date) recencia,
 count(o.order_id) frequencia,coalesce(sum(o.valor),0) valor
 FROM nw.customers c LEFT JOIN nw_analytics.vw_pedido_valor o
 ON o.customer_id=c.customer_id AND o.order_date<=DATE '1998-05-06'
 GROUP BY c.customer_id
)
SELECT *,CASE WHEN frequencia=0 THEN 0 WHEN recencia<=30 THEN 3 WHEN recencia<=90 THEN 2 ELSE 1 END r,
 CASE WHEN frequencia=0 THEN 0 WHEN frequencia>=10 THEN 3 WHEN frequencia>=5 THEN 2 ELSE 1 END f,
 CASE WHEN frequencia=0 THEN 0 WHEN valor>=10000 THEN 3 WHEN valor>=5000 THEN 2 ELSE 1 END m
FROM rfm ORDER BY customer_id;
