WITH RECURSIVE equipe AS (
 SELECT employee_id gestor_id,employee_id membro_id,ARRAY[employee_id] caminho FROM nw.employees
 UNION ALL SELECT q.gestor_id,e.employee_id,q.caminho||e.employee_id
 FROM equipe q JOIN nw.employees e ON e.reports_to=q.membro_id
 WHERE NOT e.employee_id=ANY(q.caminho)
)
SELECT q.gestor_id,count(DISTINCT q.membro_id) membros,
 coalesce(sum(v.valor) FILTER (WHERE q.membro_id=q.gestor_id),0) valor_proprio,
 count(v.order_id)::numeric pedidos_equipe,coalesce(sum(v.valor),0) valor_equipe
FROM equipe q LEFT JOIN nw_analytics.vw_pedido_valor v ON v.employee_id=q.membro_id
 AND v.order_date>=DATE '1996-07-01' AND v.order_date<DATE '1998-06-01'
GROUP BY q.gestor_id ORDER BY q.gestor_id;
