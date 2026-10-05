-- Q05 — Estoque crítico e cobertura por categoria
-- Pergunta: Quais categorias têm produtos abaixo do ponto de reposição?
-- Resultado: Categorias com produtos abaixo do ponto de reposição, déficit somado e quantos nem com o encomendado se cobrem.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
SELECT p.category_id,c.category_name categoria,count(*) produtos,
 sum(p.reorder_level-p.units_in_stock) deficit,
 count(*) FILTER (WHERE p.units_in_stock+p.units_on_order<p.reorder_level) reposicao_insuficiente,
 array_agg(p.product_id ORDER BY p.product_id) produtos_ids
FROM nw.products p JOIN nw.categories c USING(category_id)
WHERE p.units_in_stock<p.reorder_level
GROUP BY p.category_id,c.category_name ORDER BY p.category_id;
