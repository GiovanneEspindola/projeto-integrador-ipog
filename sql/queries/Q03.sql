-- Q03 — Produtos sem vendas no período
-- Pergunta: Quais produtos não foram vendidos no período?
-- Resultado: Produtos do catálogo sem nenhum item vendido na janela; lista vazia significa que todos venderam.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
SELECT p.product_id,p.product_name produto,c.category_name categoria,s.company_name fornecedor
FROM nw.products p JOIN nw.categories c USING(category_id)
JOIN nw.suppliers s USING(supplier_id)
WHERE NOT EXISTS (
 SELECT 1 FROM nw.order_items i JOIN nw.orders o USING(order_id)
 WHERE i.product_id=p.product_id AND order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01'
) ORDER BY p.product_id;
