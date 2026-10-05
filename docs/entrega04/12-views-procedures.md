# 12. Views e procedures

## 12.1 Views para relatórios

O cálculo do valor aparece em quase todas as análises. Para não repeti-lo em cada consulta, ele foi centralizado em quatro views no schema **nw_analytics**:

| View | Uma linha por | Usada em |
|---|---|---|
| vw_item_valor | item, com valor bruto, desconto e valor final | Q01, Q07, Q14, Q16 e procedure de vendas |
| vw_pedido_valor | pedido, com itens, unidades e valor | Q02, Q04, Q08 a Q11, Q15 e procedure de equipe |
| vw_vendas_mensais | mês com pedidos, com valor e ticket | Relatório direto |
| vw_envio_transportadora | transportadora, com envios, datas ausentes e média de dias | Relatório direto |

Uma view guarda a consulta, não os dados: cada leitura recalcula a partir das tabelas. As views antigas do schema nw, que arredondavam cada item, foram mantidas sem uso.

## 12.2 Procedures

Três procedures em PL/pgSQL recebem parâmetros e devolvem o resultado por um cursor. Todas validam a entrada: período invertido, número de meses não positivo e gestor inexistente são recusados com erro.

| Procedure | Parâmetros | Resultado |
|---|---|---|
| sp_resumo_vendas_periodo | início, fim | Pedidos, valor e ticket por categoria no período |
| sp_clientes_inativos | data de referência, meses | Clientes inativos e clientes sem compras |
| sp_desempenho_equipe | gestor, início, fim | Vendas próprias e da equipe do gestor |

A chamada abre uma transação, executa a procedure, lê o cursor e encerra:

```sql
BEGIN;
CALL nw_analytics.sp_clientes_inativos('1998-05-06', 6, 'inativos');
FETCH ALL FROM inativos;
COMMIT;
```

Os resultados das três foram comparados com consultas independentes. Os códigos completos estão no Apêndice B.

<!-- procedures -->
