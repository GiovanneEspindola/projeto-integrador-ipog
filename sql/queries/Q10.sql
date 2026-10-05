-- Q10 — Curva ABC de clientes
-- Pergunta: Como os clientes se distribuem pela curva ABC de valor?
-- Resultado: Todos os clientes ordenados por valor, com acumulado e classe A/B/C pela concentração do valor.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH t AS (
 SELECT c.customer_id,c.company_name cliente,count(o.order_id) pedidos,coalesce(sum(o.valor),0) valor
 FROM nw.customers c LEFT JOIN nw_analytics.vw_pedido_valor o
 ON o.customer_id=c.customer_id AND order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY c.customer_id
), a AS (
 SELECT *,sum(valor) OVER () total,
 sum(valor) OVER (ORDER BY valor DESC,customer_id ROWS UNBOUNDED PRECEDING) acumulado FROM t
)
SELECT customer_id,cliente,pedidos,valor,acumulado,
 CASE WHEN pedidos=0 THEN 'sem compras'
 WHEN acumulado-valor<total*0.80 THEN 'A'
 WHEN acumulado-valor<total*0.95 THEN 'B' ELSE 'C' END classe
FROM a ORDER BY valor DESC,customer_id;
