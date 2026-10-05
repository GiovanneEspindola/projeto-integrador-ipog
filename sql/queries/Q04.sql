-- Q04 — Indicadores por funcionário
-- Pergunta: Como se distribuem os pedidos entre os funcionários?
-- Resultado: Uma linha por funcionário, inclusive sem pedidos: pedidos, valor, valor médio por pedido e fatia do total.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH t AS (
 SELECT e.employee_id,e.first_name||' '||e.last_name funcionario,
 count(o.order_id) pedidos,coalesce(sum(o.valor),0) valor
 FROM nw.employees e LEFT JOIN nw_analytics.vw_pedido_valor o
 ON o.employee_id=e.employee_id AND order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01'
 GROUP BY e.employee_id
)
SELECT *,valor/nullif(pedidos,0) ticket,
 100*valor/nullif(sum(valor) OVER (),0) participacao
FROM t ORDER BY employee_id;
