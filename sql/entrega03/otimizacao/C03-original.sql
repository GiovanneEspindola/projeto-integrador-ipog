WITH todos AS MATERIALIZED (
 SELECT a.order_id,a.product_id produto_a,b.product_id produto_b
 FROM nw.order_items a JOIN nw.order_items b USING(order_id)
), pares AS (
 SELECT produto_a,produto_b,count(*) pedidos FROM todos JOIN nw.orders USING(order_id)
 WHERE produto_a<produto_b AND order_date>=DATE '1996-07-01' AND order_date<DATE '1998-06-01'
 GROUP BY produto_a,produto_b
), total AS (SELECT count(*) denominador FROM nw.orders WHERE order_date>=DATE '1996-07-01' AND order_date<DATE '1998-06-01')
SELECT pares.*,denominador,100.0*pedidos/nullif(denominador,0) suporte
FROM pares CROSS JOIN total ORDER BY pedidos DESC,produto_a,produto_b;
