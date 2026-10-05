-- Q16 — Distribuição trimestral por ano e categoria
-- Pergunta: Como o valor se distribui por ano, trimestre e categoria?
-- Resultado: Valor por ano e trimestre, total e por categoria, marcando trimestres com cobertura parcial dos dados.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH t AS (
 SELECT extract(year FROM order_date)::int ano,
 extract(quarter FROM order_date)::int trimestre,category_id,valor
 FROM nw_analytics.vw_item_valor WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01'
)
SELECT ano,trimestre,category_id,sum(valor) valor,
 CASE WHEN grouping(category_id)=1 THEN 'total' ELSE 'categoria' END nivel,
 (make_date(ano,(trimestre-1)*3+1,1)<DATE '1996-07-04' OR
 (make_date(ano,(trimestre-1)*3+1,1)+INTERVAL '3 months')::date>DATE '1998-05-07') parcial
FROM t GROUP BY GROUPING SETS ((ano,trimestre,category_id),(ano,trimestre))
ORDER BY ano,trimestre,category_id NULLS FIRST;
