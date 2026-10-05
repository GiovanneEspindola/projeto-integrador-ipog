-- Camada da Entrega 3. Não altera as views históricas nem os dados de nw.
CREATE SCHEMA IF NOT EXISTS nw_analytics;

CREATE OR REPLACE VIEW nw_analytics.vw_item_valor AS
SELECT i.order_id, i.product_id, o.order_date, o.customer_id,
       o.employee_id, p.category_id, i.quantity,
       i.unit_price * i.quantity AS bruto,
       i.unit_price * i.quantity * i.discount AS desconto,
       i.unit_price * i.quantity * (1-i.discount) AS valor
FROM nw.order_items i
JOIN nw.orders o USING (order_id)
JOIN nw.products p USING (product_id);

CREATE OR REPLACE VIEW nw_analytics.vw_pedido_valor AS
SELECT o.order_id, o.order_date, o.customer_id, o.employee_id,
       o.shipper_id, o.required_date, o.shipped_date,
       count(i.product_id) AS itens,
       coalesce(sum(i.quantity),0) AS unidades,
       coalesce(sum(i.unit_price*i.quantity*(1-i.discount)),0) AS valor
FROM nw.orders o LEFT JOIN nw.order_items i USING (order_id)
GROUP BY o.order_id;

CREATE OR REPLACE VIEW nw_analytics.vw_vendas_mensais AS
SELECT date_trunc('month',order_date)::date AS mes,
       count(*) AS pedidos, sum(valor) AS valor,
       sum(valor)/count(*) AS ticket
FROM nw_analytics.vw_pedido_valor GROUP BY 1;

CREATE OR REPLACE VIEW nw_analytics.vw_envio_transportadora AS
SELECT s.shipper_id, s.company_name AS transportadora,
       count(o.order_id) AS pedidos,
       count(o.shipped_date) AS com_envio,
       count(o.order_id)-count(o.shipped_date) AS sem_data,
       coalesce(sum(o.shipped_date-o.order_date),0) AS soma_dias,
       avg(o.shipped_date-o.order_date) AS media_dias,
       count(*) FILTER (WHERE o.shipped_date>o.required_date) AS apos_requerida
FROM nw.shippers s LEFT JOIN nw.orders o USING (shipper_id)
GROUP BY s.shipper_id;

COMMENT ON VIEW nw_analytics.vw_item_valor IS
'Valor exato após descontos, sem frete e sem arredondamento por item.';
COMMENT ON VIEW nw_analytics.vw_pedido_valor IS
'Uma linha por pedido; pedidos sem itens aparecem com valor zero.';
COMMENT ON VIEW nw_analytics.vw_vendas_mensais IS
'Meses com movimento; a consulta temporal completa o calendário do recorte.';
COMMENT ON VIEW nw_analytics.vw_envio_transportadora IS
'Envio registrado não comprova entrega; data nula significa ausência de registro.';
