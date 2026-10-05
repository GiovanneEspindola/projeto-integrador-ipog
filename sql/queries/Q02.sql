-- Q02 — Pedidos e ticket médio mensal
-- Pergunta: Como variam o número de pedidos e o ticket médio mensal?
-- Resultado: Uma linha por mês, inclusive sem pedidos: quantidade de pedidos, valor e valor médio por pedido.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH calendario AS (
 SELECT generate_series(DATE '1996-07-01', DATE '1998-06-01'-INTERVAL '1 month', INTERVAL '1 month')::date mes
), totais AS (
 SELECT date_trunc('month',order_date)::date mes, count(*) pedidos, sum(valor) valor
 FROM nw_analytics.vw_pedido_valor WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY 1
), mensal AS (
 SELECT c.mes,coalesce(t.pedidos,0) pedidos,coalesce(t.valor,0) valor
 FROM calendario c LEFT JOIN totais t USING(mes)
)
SELECT mes,pedidos,valor,valor/nullif(pedidos,0) ticket FROM mensal ORDER BY mes;
