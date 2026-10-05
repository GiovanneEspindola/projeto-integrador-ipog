-- Q06 — Clientes inativos e sem compras
-- Pergunta: Quais clientes estão sem compra há mais de seis meses?
-- Resultado: Clientes sem compra desde antes de 06/11/1997 (inativos) e clientes que nunca compraram.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH historico AS (
 SELECT c.customer_id,c.company_name cliente,max(o.order_date) ultima
 FROM nw.customers c LEFT JOIN nw.orders o ON o.customer_id=c.customer_id
 AND o.order_date<=DATE '1998-05-06' GROUP BY c.customer_id
)
SELECT *,DATE '1998-05-06'-ultima recencia,
 CASE WHEN ultima IS NULL THEN 'sem compras' ELSE 'inativo' END situacao
FROM historico WHERE ultima IS NULL OR ultima<DATE '1997-11-06'
ORDER BY customer_id;
