BEGIN;
CALL nw_analytics.sp_resumo_vendas_periodo(
    '1996-07-01','1998-06-01','vendas');
FETCH ALL FROM vendas;
CALL nw_analytics.sp_clientes_inativos('1998-05-06',6,'inativos');
FETCH ALL FROM inativos;
CALL nw_analytics.sp_desempenho_equipe(2,'1996-07-01','1998-06-01','equipe');
FETCH ALL FROM equipe;
COMMIT;
