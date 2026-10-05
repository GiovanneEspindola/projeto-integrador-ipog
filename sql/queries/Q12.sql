-- Q12 — Produtos comprados juntos
-- Pergunta: Quais produtos aparecem juntos no mesmo pedido?
-- Resultado: Pares de produtos que aparecem no mesmo pedido, quantos pedidos contêm cada par e o suporte (%).
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH pares AS (
 SELECT a.product_id produto_a,b.product_id produto_b,count(*) pedidos
 FROM nw.orders o JOIN nw.order_items a USING(order_id)
 JOIN nw.order_items b ON b.order_id=a.order_id AND a.product_id<b.product_id
 WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY a.product_id,b.product_id
), total AS (SELECT count(*) denominador FROM nw.orders WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01')
SELECT pares.*,total.denominador,100.0*pedidos/nullif(denominador,0) suporte
FROM pares CROSS JOIN total ORDER BY pedidos DESC,produto_a,produto_b;
