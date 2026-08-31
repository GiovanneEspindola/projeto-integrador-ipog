-- =============================================================================
-- 40_views.sql — views analíticas do schema nw
-- =============================================================================
-- Quatro views, nenhuma decorativa. Cada uma existe porque um cálculo se
-- repetiria em várias consultas das Entregas 03 e 04, e cálculo repetido é
-- cálculo que uma hora sai diferente em algum lugar.
--
--   docker compose exec -T postgres psql -U pi -d northwind -f /sql/40_views.sql
-- =============================================================================

SET search_path TO nw;

-- -----------------------------------------------------------------------------
-- vw_venda_item — a linha de venda com tudo que ela significa
-- -----------------------------------------------------------------------------
-- PERGUNTA QUE RESPONDE: base das perguntas 01, 04, 07, 10, 11, 14 e 16.
-- O QUE O RESULTADO SIGNIFICA: uma linha por produto vendido, já com o valor
-- em reais e com os nomes de categoria, cliente e vendedor ao lado — para não
-- reescrever a mesma junção de cinco tabelas em toda consulta.
--
-- A receita é arredondada POR ITEM, não no fim da soma: cada linha de venda
-- tem um valor real em centavos, e é ele que se soma. Arredondar só no total
-- produziria um número que não bate com a soma das linhas.
CREATE OR REPLACE VIEW vw_venda_item AS
SELECT
    i.order_id,
    i.product_id,
    o.order_date,
    o.customer_id,
    cl.company_name                                     AS cliente,
    o.employee_id,
    e.first_name || ' ' || e.last_name                  AS vendedor,
    p.product_name                                      AS produto,
    c.category_id,
    c.category_name                                     AS categoria,
    p.supplier_id,
    i.quantity,
    i.unit_price                                        AS preco_praticado,
    p.unit_price                                        AS preco_catalogo_hoje,
    i.discount                                          AS desconto,
    round(i.unit_price * i.quantity, 2)                 AS receita_bruta,
    round(i.unit_price * i.quantity * i.discount, 2)    AS valor_do_desconto,
    round(i.unit_price * i.quantity * (1 - i.discount), 2) AS receita
FROM order_items i
JOIN orders     o  ON o.order_id    = i.order_id
JOIN products   p  ON p.product_id  = i.product_id
JOIN categories c  ON c.category_id = p.category_id
JOIN customers  cl ON cl.customer_id = o.customer_id
JOIN employees  e  ON e.employee_id = o.employee_id;

COMMENT ON VIEW vw_venda_item IS
  'Uma linha por produto vendido, com receita já calculada e as dimensões ao lado. É a base da maioria das análises.';

-- -----------------------------------------------------------------------------
-- vw_pedido_resumo — o pedido visto de cima
-- -----------------------------------------------------------------------------
-- PERGUNTA QUE RESPONDE: perguntas 02 (ticket médio), 06 (clientes inativos) e
-- 13 (prazo de entrega por transportadora).
-- O QUE O RESULTADO SIGNIFICA: uma linha por pedido com quantos itens tem,
-- quanto valeu e quantos dias levou para sair. dias_para_envio NULO significa
-- pedido ainda não enviado — não é dado faltando.
CREATE OR REPLACE VIEW vw_pedido_resumo AS
SELECT
    o.order_id,
    o.order_date,
    o.customer_id,
    cl.company_name                          AS cliente,
    cl.country                               AS pais_cliente,
    o.employee_id,
    e.first_name || ' ' || e.last_name       AS vendedor,
    o.shipper_id,
    s.company_name                           AS transportadora,
    o.freight                                AS frete,
    count(i.product_id)                      AS itens,
    sum(i.quantity)                          AS unidades,
    sum(round(i.unit_price * i.quantity * (1 - i.discount), 2)) AS valor_pedido,
    o.shipped_date,
    o.shipped_date - o.order_date            AS dias_para_envio,
    o.required_date - o.order_date           AS prazo_prometido_dias,
    o.shipped_date > o.required_date         AS entregue_com_atraso
FROM orders     o
JOIN customers  cl ON cl.customer_id = o.customer_id
JOIN employees  e  ON e.employee_id  = o.employee_id
JOIN shippers   s  ON s.shipper_id   = o.shipper_id
JOIN order_items i ON i.order_id     = o.order_id
GROUP BY o.order_id, cl.company_name, cl.country, e.first_name, e.last_name,
         s.company_name;

COMMENT ON VIEW vw_pedido_resumo IS
  'Uma linha por pedido: valor total, contagem de itens e prazos. dias_para_envio nulo = pedido nunca enviado.';

-- -----------------------------------------------------------------------------
-- vw_estoque_critico — o que precisa ser reposto
-- -----------------------------------------------------------------------------
-- PERGUNTA QUE RESPONDE: pergunta 05.
-- O QUE O RESULTADO SIGNIFICA: produtos cujo estoque já caiu abaixo do ponto de
-- reposição. A coluna cobertura diz se o que está encomendado resolve: se
-- estoque + encomendado ainda ficar abaixo do ponto, a reposição é insuficiente.
CREATE OR REPLACE VIEW vw_estoque_critico AS
SELECT
    p.product_id,
    p.product_name                AS produto,
    c.category_name               AS categoria,
    s.company_name                AS fornecedor,
    p.units_in_stock              AS estoque,
    p.units_on_order              AS encomendado,
    p.reorder_level               AS ponto_de_reposicao,
    p.units_in_stock + p.units_on_order - p.reorder_level AS folga_apos_chegada,
    CASE
        WHEN p.units_in_stock + p.units_on_order >= p.reorder_level THEN 'reposição a caminho'
        ELSE 'reposição insuficiente'
    END                           AS cobertura,
    p.discontinued                AS fora_de_linha
FROM products   p
JOIN categories c ON c.category_id = p.category_id
JOIN suppliers  s ON s.supplier_id = p.supplier_id
WHERE p.units_in_stock < p.reorder_level;

COMMENT ON VIEW vw_estoque_critico IS
  'Produtos abaixo do ponto de reposição, com o julgamento de se o pedido de compra em aberto resolve.';

-- -----------------------------------------------------------------------------
-- vw_hierarquia_funcionarios — quem responde a quem
-- -----------------------------------------------------------------------------
-- PERGUNTA QUE RESPONDE: base da pergunta 15 (vendas da equipe de cada gerente).
-- O QUE O RESULTADO SIGNIFICA: cada funcionário com seu nível na hierarquia e o
-- caminho até o topo. É uma CTE RECURSIVA: a consulta se chama de volta,
-- descendo um nível por vez, até acabarem os subordinados. Sem recursão seria
-- preciso saber de antemão quantos níveis a empresa tem.
CREATE OR REPLACE VIEW vw_hierarquia_funcionarios AS
WITH RECURSIVE arvore AS (
    SELECT  e.employee_id,
            e.first_name || ' ' || e.last_name AS funcionario,
            e.title                            AS cargo,
            e.reports_to,
            1                                  AS nivel,
            ARRAY[e.employee_id]               AS caminho
      FROM  employees e
     WHERE  e.reports_to IS NULL

    UNION ALL

    SELECT  e.employee_id,
            e.first_name || ' ' || e.last_name,
            e.title,
            e.reports_to,
            a.nivel + 1,
            a.caminho || e.employee_id
      FROM  employees e
      JOIN  arvore a ON a.employee_id = e.reports_to
)
SELECT  a.employee_id,
        a.funcionario,
        a.cargo,
        a.nivel,
        a.reports_to                          AS chefe_id,
        ch.first_name || ' ' || ch.last_name  AS chefe,
        a.caminho
  FROM  arvore a
  LEFT JOIN employees ch ON ch.employee_id = a.reports_to;

COMMENT ON VIEW vw_hierarquia_funcionarios IS
  'Hierarquia da equipe resolvida por CTE recursiva: nível de cada funcionário e o caminho até o topo.';
