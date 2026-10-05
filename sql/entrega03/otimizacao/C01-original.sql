SELECT date_trunc('month',order_date)::date mes,count(*) pedidos,sum(valor) valor
FROM nw_analytics.vw_pedido_valor
WHERE to_char(order_date,'YYYY-MM')='1997-01' GROUP BY 1 ORDER BY 1;
