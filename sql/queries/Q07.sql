-- Q07 — Top cinco produtos por categoria
-- Pergunta: Quais são os cinco produtos de maior valor em cada categoria?
-- Resultado: Até cinco produtos de maior valor em cada categoria, com posição 1 a 5 e desempate pelo menor ID.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH t AS (
 SELECT category_id,product_id,sum(valor) valor FROM nw_analytics.vw_item_valor
 WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY category_id,product_id
), ranking AS (
 SELECT *,row_number() OVER (PARTITION BY category_id ORDER BY valor DESC,product_id) posicao FROM t
)
SELECT category_id,product_id,valor,posicao FROM ranking WHERE posicao<=5 ORDER BY category_id,posicao;
