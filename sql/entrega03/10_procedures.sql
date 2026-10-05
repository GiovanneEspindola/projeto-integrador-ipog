-- Relatórios tabulares: abrir transação, CALL, FETCH e COMMIT.
CREATE OR REPLACE PROCEDURE nw_analytics.sp_resumo_vendas_periodo(
    IN inicio date, IN fim date, INOUT resultado refcursor)
LANGUAGE plpgsql AS $$
BEGIN
    IF inicio IS NULL OR fim IS NULL OR inicio>=fim THEN
        RAISE EXCEPTION 'Informe início anterior ao fim exclusivo';
    END IF;
    OPEN resultado FOR
    SELECT i.category_id,c.category_name categoria,
           count(DISTINCT i.order_id) pedidos,sum(i.valor) valor,
           sum(i.valor)/count(DISTINCT i.order_id) ticket_categoria
    FROM nw_analytics.vw_item_valor i
    JOIN nw.categories c USING(category_id)
    WHERE i.order_date>=inicio AND i.order_date<fim
    GROUP BY i.category_id,c.category_name ORDER BY i.category_id;
END;
$$;

CREATE OR REPLACE PROCEDURE nw_analytics.sp_clientes_inativos(
    IN referencia date, IN meses integer, INOUT resultado refcursor)
LANGUAGE plpgsql AS $$
BEGIN
    IF referencia IS NULL OR meses IS NULL OR meses<1 THEN
        RAISE EXCEPTION 'Informe referência e meses positivos';
    END IF;
    OPEN resultado FOR
    WITH historico AS (
        SELECT c.customer_id,c.company_name cliente,max(o.order_date) ultima
        FROM nw.customers c LEFT JOIN nw.orders o
          ON o.customer_id=c.customer_id AND o.order_date<=referencia
        GROUP BY c.customer_id
    )
    SELECT *,referencia-ultima recencia,
           CASE WHEN ultima IS NULL THEN 'sem compras' ELSE 'inativo' END situacao
    FROM historico
    WHERE ultima IS NULL OR ultima<(referencia-make_interval(months=>meses))::date
    ORDER BY customer_id;
END;
$$;

CREATE OR REPLACE PROCEDURE nw_analytics.sp_desempenho_equipe(
    IN gestor integer, IN inicio date, IN fim date, INOUT resultado refcursor)
LANGUAGE plpgsql AS $$
BEGIN
    IF inicio IS NULL OR fim IS NULL OR inicio>=fim THEN
        RAISE EXCEPTION 'Informe início anterior ao fim exclusivo';
    END IF;
    IF gestor IS NULL OR NOT EXISTS (
        SELECT 1 FROM nw.employees WHERE employee_id=gestor
    ) THEN RAISE EXCEPTION 'Gestor inexistente'; END IF;
    OPEN resultado FOR
    WITH RECURSIVE equipe AS (
        SELECT employee_id,ARRAY[employee_id] caminho
        FROM nw.employees WHERE employee_id=gestor
        UNION ALL
        SELECT e.employee_id,q.caminho||e.employee_id
        FROM equipe q JOIN nw.employees e ON e.reports_to=q.employee_id
        WHERE NOT e.employee_id=ANY(q.caminho)
    ), vendas AS (
        SELECT employee_id,count(*) pedidos,sum(valor) valor
        FROM nw_analytics.vw_pedido_valor
        WHERE order_date>=inicio AND order_date<fim GROUP BY employee_id
    )
    SELECT gestor gestor_id,count(*) membros,
           coalesce(sum(v.valor) FILTER (WHERE q.employee_id=gestor),0) valor_proprio,
           coalesce(sum(v.pedidos),0) pedidos_equipe,
           coalesce(sum(v.valor),0) valor_equipe
    FROM equipe q LEFT JOIN vendas v USING(employee_id);
END;
$$;
