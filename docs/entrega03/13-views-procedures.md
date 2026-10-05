# 13. Views e procedimentos armazenados

As quatro novas views compõem uma camada de relatórios em nw_analytics. vw_item_valor calcula bruto, desconto e valor exato por item; vw_pedido_valor reúne contagens e valor por pedido; vw_vendas_mensais resume os meses com movimento; vw_envio_transportadora apresenta pedidos, datas ausentes e intervalo até envio. O calendário completo é construído nas consultas temporais.

Uma view armazena a definição da consulta, não uma cópia materializada dos resultados. Sua finalidade é centralizar a regra de valor para que todas as análises a apliquem da mesma forma. vw_item_valor alimenta Q01, Q07, Q14 e Q16; vw_pedido_valor alimenta Q02, Q04, Q08 a Q11 e Q15. As outras duas podem ser consultadas diretamente como relatórios prontos, por exemplo SELECT * FROM nw_analytics.vw_envio_transportadora. As views antigas de nw, que arredondam por item, foram mantidas sem alteração e não são usadas nos valores da Entrega 3.

## 13.1 Procedures parametrizadas

Foram implementadas três procedures PL/pgSQL [13]. sp_resumo_vendas_periodo recebe início/fim e retorna, por categoria, pedidos distintos, valor e ticket. Um pedido com mais de uma categoria conta em cada categoria; não se somam essas contagens como se fossem pedidos distintos do conjunto. sp_clientes_inativos recebe a data de referência e o número de meses. sp_desempenho_equipe recebe gestor e período e retorna vendas próprias e da equipe.

Os relatórios tabulares usam um parâmetro INOUT refcursor. Esse parâmetro recebe o nome de um cursor: a procedure abre o cursor com o resultado, e o cliente o lê com FETCH na mesma transação, como no exemplo do Apêndice B. As três rotinas foram criadas com CREATE PROCEDURE e são executadas com CALL; no PostgreSQL, funções (CREATE FUNCTION) são objetos diferentes, chamados dentro de consultas.

Períodos invertidos, quantidade de meses não positiva e gestor inexistente são rejeitados. Os três resultados foram comparados com consultas independentes. Para o gestor 2, a procedure retorna nove membros, 830 pedidos e o valor total da base, porque toda a hierarquia está abaixo dele; os pedidos de cada membro entram uma única vez.

As definições completas das views, das procedures e das chamadas estão no Apêndice B. Nas saídas abaixo, os decimais foram arredondados para duas casas apenas na apresentação.

<!-- procedures -->
