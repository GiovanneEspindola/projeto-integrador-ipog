-- Q15 — Vendas próprias e da equipe
-- Pergunta: Quanto foi registrado por cada funcionário e sua equipe?
-- Resultado: Por funcionário: tamanho da equipe (ele e subordinados), valor próprio e valor da equipe; equipes se sobrepõem.
-- Intervalo [1996-07-01, 1998-06-01); RFM/inatividade: 1998-05-06.
WITH RECURSIVE equipe AS (
 SELECT employee_id gestor_id,employee_id membro_id,ARRAY[employee_id] caminho FROM nw.employees
 UNION ALL
 SELECT q.gestor_id,e.employee_id,q.caminho||e.employee_id
 FROM equipe q JOIN nw.employees e ON e.reports_to=q.membro_id
 WHERE NOT e.employee_id=ANY(q.caminho)
), vendas AS (
 SELECT employee_id,count(*) pedidos,sum(valor) valor
 FROM nw_analytics.vw_pedido_valor WHERE order_date >= DATE '1996-07-01' AND order_date < DATE '1998-06-01' GROUP BY employee_id
)
SELECT q.gestor_id,count(*) membros,
 coalesce(sum(v.valor) FILTER (WHERE q.membro_id=q.gestor_id),0) valor_proprio,
 coalesce(sum(v.pedidos),0) pedidos_equipe,coalesce(sum(v.valor),0) valor_equipe
FROM equipe q LEFT JOIN vendas v ON v.employee_id=q.membro_id
GROUP BY q.gestor_id ORDER BY q.gestor_id;

