-- Q14 — Descontos sobre o valor dos pedidos
-- Pergunta: Quanto os descontos reduzem o valor bruto dos itens?
-- Resultado: Por categoria: valor bruto, desconto concedido, valor após descontos e taxa ponderada de desconto.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
SELECT category_id,sum(bruto) bruto,sum(desconto) desconto,sum(valor) valor,
 100*sum(desconto)/nullif(sum(bruto),0) percentual_desconto
FROM nw_analytics.vw_item_valor WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01'
GROUP BY category_id ORDER BY category_id;
