-- Q13 — Intervalo até envio por transportadora
-- Pergunta: Qual é o intervalo até o envio registrado por transportadora?
-- Resultado: Por transportadora: pedidos, datas de envio registradas e ausentes, média de dias até o envio e envios após a data requerida.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
SELECT s.shipper_id,s.company_name transportadora,count(o.order_id) pedidos,
 count(o.shipped_date) com_envio,count(o.order_id)-count(o.shipped_date) sem_data,
 coalesce(sum(o.shipped_date-o.order_date),0) soma_dias,
 avg(o.shipped_date-o.order_date) media_dias,
 count(*) FILTER (WHERE o.shipped_date>o.required_date) apos_requerida
FROM nw.shippers s LEFT JOIN nw.orders o ON o.shipper_id=s.shipper_id AND order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01'
GROUP BY s.shipper_id ORDER BY s.shipper_id;
