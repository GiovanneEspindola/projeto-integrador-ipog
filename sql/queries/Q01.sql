-- Q01 — Valor e participação por categoria
-- Pergunta: Quais categorias concentram o valor dos pedidos?
-- Resultado: Uma linha por categoria com vendas: unidades, valor após descontos e fatia (%) do valor total.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH totais AS (
 SELECT category_id,sum(quantity) unidades,sum(valor) valor
 FROM nw_analytics.vw_item_valor WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY category_id
)
SELECT t.category_id,c.category_name categoria,t.unidades,t.valor,
       100*t.valor/nullif(sum(t.valor) OVER (),0) participacao
FROM totais t JOIN nw.categories c USING(category_id)
ORDER BY t.category_id;
