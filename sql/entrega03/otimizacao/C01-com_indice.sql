SELECT date_trunc('month',order_date)::date mes,count(*) pedidos,sum(valor) valor
FROM nw_analytics.vw_pedido_valor
WHERE order_date>=DATE '1997-01-01' AND order_date<DATE '1997-02-01' GROUP BY 1 ORDER BY 1;
