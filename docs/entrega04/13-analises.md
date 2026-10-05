# 13. Consultas analíticas e resultados

Cada seção traz a pergunta, a regra de cálculo, os recursos usados em cada banco, o resultado e o que ele significa. As tabelas mostram a saída validada, idêntica nos dois bancos, com decimais arredondados só na apresentação. Quando o resultado é longo, o recorte exibido está indicado. Os 32 códigos completos estão no Apêndice A.

## 13.1 Q01/P01 — Valor e participação por categoria

**Pergunta:** Quais categorias concentram o valor dos pedidos?

**Cálculo:** Relacionar itens ao pedido e à categoria, somar quantidade e valor e dividir cada valor pelo total geral.

**Recursos:** SQL: JOIN, GROUP BY e SUM OVER. MongoDB: $unwind, $group e $setWindowFields.

**Resultado:** 8 linhas; todas exibidas.

| categoria (ID) | categoria | unidades | valor | participação (%) |
| --- | --- | --- | --- | --- |
| 1 | Beverages | 9532 | 267.868,18 | 21,16 |
| 2 | Condiments | 5298 | 106.047,09 | 8,38 |
| 3 | Confections | 7906 | 167.357,23 | 13,22 |
| 4 | Dairy Products | 9149 | 234.507,29 | 18,53 |
| 5 | Grains/Cereals | 4562 | 95.744,59 | 7,56 |
| 6 | Meat/Poultry | 4199 | 163.022,36 | 12,88 |
| 7 | Produce | 2990 | 99.984,58 | 7,90 |
| 8 | Seafood | 7681 | 131.261,74 | 10,37 |

**Leitura:** Beverages lidera com 21,16% do valor (267.868,18), seguida por Dairy Products com 18,53%. Juntas, as duas categorias somam quase 40% de tudo o que foi vendido.

**Cuidado:** A participação mede peso no valor dos pedidos, não rentabilidade. Os grupos são definidos pelo ID da categoria e o percentual é calculado depois da agregação, sobre o mesmo recorte.

## 13.2 Q02/P02 — Pedidos e ticket médio mensal

**Pergunta:** Como variam o número de pedidos e o ticket médio mensal?

**Cálculo:** Somar itens por pedido, agrupar pedidos por mês e completar o calendário. Ticket = valor / pedidos.

**Recursos:** SQL: CTEs, generate_series e agregação em dois níveis. MongoDB: $map, $group, $facet e calendário por $dateAdd.

**Resultado:** 23 linhas; todas exibidas.

| mês | pedidos | valor | ticket |
| --- | --- | --- | --- |
| 1996-07-01 | 22 | 27.861,90 | 1.266,45 |
| 1996-08-01 | 25 | 25.485,28 | 1.019,41 |
| 1996-09-01 | 23 | 26.381,40 | 1.147,02 |
| 1996-10-01 | 26 | 37.515,73 | 1.442,91 |
| 1996-11-01 | 25 | 45.600,05 | 1.824,00 |
| 1996-12-01 | 31 | 45.239,63 | 1.459,34 |
| 1997-01-01 | 33 | 61.258,07 | 1.856,31 |
| 1997-02-01 | 29 | 38.483,64 | 1.327,02 |
| 1997-03-01 | 30 | 38.547,22 | 1.284,91 |
| 1997-04-01 | 31 | 53.032,95 | 1.710,74 |
| 1997-05-01 | 32 | 53.781,29 | 1.680,67 |
| 1997-06-01 | 30 | 36.362,80 | 1.212,09 |
| 1997-07-01 | 33 | 51.020,86 | 1.546,09 |
| 1997-08-01 | 33 | 47.287,67 | 1.432,96 |
| 1997-09-01 | 37 | 55.629,24 | 1.503,49 |
| 1997-10-01 | 38 | 66.749,23 | 1.756,56 |
| 1997-11-01 | 34 | 43.533,81 | 1.280,41 |
| 1997-12-01 | 48 | 71.398,43 | 1.487,47 |
| 1998-01-01 | 55 | 94.222,11 | 1.713,13 |
| 1998-02-01 | 54 | 99.415,29 | 1.841,02 |
| 1998-03-01 | 73 | 104.854,16 | 1.436,36 |
| 1998-04-01 | 74 | 123.798,68 | 1.672,96 |
| 1998-05-01 | 14 | 18.333,63 | 1.309,55 |

<!-- image:apresentacao/evidencias/entrega04/mensal.png -->

Figura 4 — Valor mensal após descontos (Q02/P02). Julho de 1996 começa no dia 4 e maio de 1998 termina no dia 6.

**Leitura:** O volume mensal mais que dobrou entre o início e o fim da série: de 33 pedidos em janeiro de 1997 para 74 em abril de 1998, o maior valor mensal (123.798,68). Maio de 1998 aparece baixo porque a base termina no dia 6.

**Cuidado:** O ticket é calculado por pedido: a média dos valores dos itens mediria o item médio, não o pedido médio. Um mês sem pedidos teria valor zero e ticket indefinido (nulo).

## 13.3 Q03/P03 — Produtos sem vendas no período

**Pergunta:** Quais produtos não foram vendidos no período?

**Cálculo:** Começar pelo cadastro completo e verificar se existe pelo menos um item em pedido dentro da janela.

**Recursos:** SQL: NOT EXISTS e junções cadastrais. MongoDB: $lookup com $limit e filtro de array vazio.

**Resultado:** nenhuma linha nos dois bancos.

**Leitura:** Nenhum produto ficou sem venda: os 77 aparecem em pelo menos um pedido do período. Um resultado vazio também é uma resposta.

**Cuidado:** O resultado vazio vale apenas para o recorte completo; em janelas menores podem surgir produtos sem venda. Os testes sintéticos confirmam que a consulta lista esses produtos quando existem.

## 13.4 Q04/P04 — Indicadores por funcionário

**Pergunta:** Como se distribuem os pedidos entre os funcionários?

**Cálculo:** Preservar o cadastro de funcionários, somar pedidos e valor de cada um e calcular ticket e participação.

**Recursos:** SQL: LEFT JOIN, agregação e janela global. MongoDB: $lookup, $group e $setWindowFields.

**Resultado:** 9 linhas; todas exibidas.

| funcionário (ID) | funcionário | pedidos | valor | ticket | participação (%) |
| --- | --- | --- | --- | --- | --- |
| 1 | Nancy Davolio | 123 | 192.107,60 | 1.561,85 | 15,18 |
| 2 | Andrew Fuller | 96 | 166.537,76 | 1.734,77 | 13,16 |
| 3 | Janet Leverling | 127 | 202.812,84 | 1.596,95 | 16,02 |
| 4 | Margaret Peacock | 156 | 232.890,85 | 1.492,89 | 18,40 |
| 5 | Steven Buchanan | 42 | 68.792,28 | 1.637,91 | 5,43 |
| 6 | Michael Suyama | 67 | 73.913,13 | 1.103,18 | 5,84 |
| 7 | Robert King | 72 | 124.568,24 | 1.730,11 | 9,84 |
| 8 | Laura Callahan | 104 | 126.862,28 | 1.219,83 | 10,02 |
| 9 | Anne Dodsworth | 43 | 77.308,07 | 1.797,86 | 6,11 |

**Leitura:** Margaret Peacock tem o maior valor registrado: 232.890,85 em 156 pedidos, 18,40% do total. Sem dados de carteira ou território, a comparação descreve vendas, e não produtividade.

**Cuidado:** Os valores descrevem vendas registradas por funcionário. Sem informação de carteira, território ou tempo de atuação, a diferença entre eles não mede produtividade.

## 13.5 Q05/P05 — Estoque crítico e cobertura por categoria

**Pergunta:** Quais categorias têm produtos abaixo do ponto de reposição?

**Cálculo:** Comparar estoque com reorder_level, somar a diferença e verificar se estoque mais encomendado cobre o ponto.

**Recursos:** SQL: Comparação entre colunas, FILTER e array_agg. MongoDB: $expr, $set, $group e $push.

**Resultado:** 7 linhas; todas exibidas.

| categoria (ID) | categoria | produtos | déficit | cobertura insuficiente | produtos (IDs) |
| --- | --- | --- | --- | --- | --- |
| 1 | Beverages | 3 | 31 | 1 | 2, 43, 70 |
| 2 | Condiments | 2 | 28 | 0 | 3, 66 |
| 3 | Confections | 4 | 26 | 0 | 21, 48, 49, 68 |
| 4 | Dairy Products | 3 | 44 | 0 | 11, 31, 32 |
| 5 | Grains/Cereals | 2 | 17 | 0 | 56, 64 |
| 7 | Produce | 1 | 1 | 0 | 74 |
| 8 | Seafood | 3 | 29 | 1 | 30, 37, 45 |

**Leitura:** Há 18 produtos abaixo do ponto, em sete categorias. Em dois deles, nem o estoque somado ao encomendado alcança o ponto. Um dos 18, Chang (ID 2), está descontinuado, o que mostra por que o sinal precisa ser conferido antes de uma compra.

**Cuidado:** O estoque é o estado cadastrado, sem reconstrução histórica. O indicador precisa ser conferido com o status do produto antes de virar recomendação de compra.

## 13.6 Q06/P06 — Clientes inativos e sem compras

**Pergunta:** Quais clientes estão sem compra há mais de seis meses?

**Cálculo:** Para cada cliente, obter a última compra até 06/05/1998. Selecionar data anterior a 06/11/1997 ou ausência de compras.

**Recursos:** SQL: LEFT JOIN, MAX e comparação de datas. MongoDB: $lookup, $dateDiff e tratamento de null.

**Resultado:** 7 linhas; todas exibidas.

| cliente (código) | cliente | última compra | recência (dias) | situação |
| --- | --- | --- | --- | --- |
| CENTC | Centro comercial Moctezuma | 1996-07-18 | 657 | inativo |
| FAMIA | Familia Arquibaldo | 1997-10-31 | 187 | inativo |
| FISSA | FISSA Fabrica Inter. Salchichas S.A. | — | — | sem compras |
| HUNGC | Hungry Coyote Import Store | 1997-09-08 | 240 | inativo |
| LAZYK | Lazy K Kountry Store | 1997-05-22 | 349 | inativo |
| MEREP | Mère Paillarde | 1997-10-30 | 188 | inativo |
| PARIS | Paris spécialités | — | — | sem compras |

**Leitura:** Cinco clientes não compram desde antes do corte e dois nunca compraram (FISSA e PARIS). Entre os inativos está MEREP, nono maior cliente em valor e classe A na curva ABC, sem compras desde 30/10/1997.

**Cuidado:** A referência 06/05/1998 é o último pedido da base; a data atual tornaria todos os clientes inativos. Seis meses de calendário não equivalem necessariamente a 180 dias.

## 13.7 Q07/P07 — Top cinco produtos por categoria

**Pergunta:** Quais são os cinco produtos de maior valor em cada categoria?

**Cálculo:** Agregar por produto e categoria, ordenar por valor decrescente e ID crescente, numerar dentro de cada categoria e manter posições de 1 a 5.

**Recursos:** SQL: ROW_NUMBER com PARTITION BY. MongoDB: $setWindowFields e soma cumulativa de 1.

**Resultado:** 40 linhas; exibido o primeiro colocado de cada categoria.

| categoria (ID) | produto (ID) | valor | posição |
| --- | --- | --- | --- |
| 1 | 38 | 141.396,74 | 1 |
| 2 | 63 | 16.701,10 | 1 |
| 3 | 62 | 47.234,97 | 1 |
| 4 | 59 | 71.155,70 | 1 |
| 5 | 56 | 42.593,06 | 1 |
| 6 | 29 | 80.368,67 | 1 |
| 7 | 51 | 41.819,65 | 1 |
| 8 | 18 | 29.171,88 | 1 |

**Leitura:** O produto 38 (Côte de Blaye) lidera Beverages com 141.396,74, cerca de seis vezes o segundo colocado da categoria e 52,79% do valor de Beverages. Sozinho, ele responde por 11,17% do valor total do período, o que torna a categoria dependente de um único item.

**Cuidado:** O ranking é por valor, não por unidades vendidas. Com ROW_NUMBER, empates na quinta posição são resolvidos pelo menor ID; RANK poderia devolver mais de cinco linhas.

## 13.8 Q08/P08 — Valor mensal acumulado

**Pergunta:** Qual é o valor acumulado ao longo dos meses?

**Cálculo:** Construir a série mensal e somar os valores da primeira linha até a linha corrente.

**Recursos:** SQL: SUM OVER com ROWS UNBOUNDED PRECEDING. MongoDB: $setWindowFields com janela até current.

**Resultado:** 23 linhas; todas exibidas.

| mês | valor | acumulado |
| --- | --- | --- |
| 1996-07-01 | 27.861,90 | 27.861,90 |
| 1996-08-01 | 25.485,28 | 53.347,17 |
| 1996-09-01 | 26.381,40 | 79.728,57 |
| 1996-10-01 | 37.515,73 | 117.244,30 |
| 1996-11-01 | 45.600,05 | 162.844,34 |
| 1996-12-01 | 45.239,63 | 208.083,97 |
| 1997-01-01 | 61.258,07 | 269.342,04 |
| 1997-02-01 | 38.483,64 | 307.825,68 |
| 1997-03-01 | 38.547,22 | 346.372,90 |
| 1997-04-01 | 53.032,95 | 399.405,85 |
| 1997-05-01 | 53.781,29 | 453.187,14 |
| 1997-06-01 | 36.362,80 | 489.549,94 |
| 1997-07-01 | 51.020,86 | 540.570,80 |
| 1997-08-01 | 47.287,67 | 587.858,47 |
| 1997-09-01 | 55.629,24 | 643.487,71 |
| 1997-10-01 | 66.749,23 | 710.236,94 |
| 1997-11-01 | 43.533,81 | 753.770,75 |
| 1997-12-01 | 71.398,43 | 825.169,17 |
| 1998-01-01 | 94.222,11 | 919.391,28 |
| 1998-02-01 | 99.415,29 | 1.018.806,57 |
| 1998-03-01 | 104.854,16 | 1.123.660,73 |
| 1998-04-01 | 123.798,68 | 1.247.459,41 |
| 1998-05-01 | 18.333,63 | 1.265.793,04 |

**Leitura:** O acumulado termina em 1.265.793,04, o mesmo total calculado diretamente sobre os itens, o que confirma que nenhum mês ficou de fora ou foi contado duas vezes.

**Cuidado:** Um acumulado crescente não indica crescimento mensal: ele sobe sempre que o mês tem valor positivo. O total é a última linha, não a soma dos acumulados.

## 13.9 Q09/P09 — Variação mensal do valor

**Pergunta:** Quanto o valor mudou em relação ao mês anterior?

**Cálculo:** Obter o valor do mês anterior, subtrair do atual e dividir a diferença pelo anterior.

**Recursos:** SQL: LAG e NULLIF. MongoDB: $shift e $cond.

**Resultado:** 23 linhas; todas exibidas.

| mês | valor | mês anterior | variação | variação (%) |
| --- | --- | --- | --- | --- |
| 1996-07-01 | 27.861,90 | — | — | — |
| 1996-08-01 | 25.485,28 | 27.861,90 | -2.376,62 | -8,53 |
| 1996-09-01 | 26.381,40 | 25.485,28 | 896,13 | 3,52 |
| 1996-10-01 | 37.515,73 | 26.381,40 | 11.134,33 | 42,21 |
| 1996-11-01 | 45.600,05 | 37.515,73 | 8.084,32 | 21,55 |
| 1996-12-01 | 45.239,63 | 45.600,05 | -360,42 | -0,79 |
| 1997-01-01 | 61.258,07 | 45.239,63 | 16.018,44 | 35,41 |
| 1997-02-01 | 38.483,64 | 61.258,07 | -22.774,44 | -37,18 |
| 1997-03-01 | 38.547,22 | 38.483,64 | 63,59 | 0,17 |
| 1997-04-01 | 53.032,95 | 38.547,22 | 14.485,73 | 37,58 |
| 1997-05-01 | 53.781,29 | 53.032,95 | 748,34 | 1,41 |
| 1997-06-01 | 36.362,80 | 53.781,29 | -17.418,49 | -32,39 |
| 1997-07-01 | 51.020,86 | 36.362,80 | 14.658,06 | 40,31 |
| 1997-08-01 | 47.287,67 | 51.020,86 | -3.733,19 | -7,32 |
| 1997-09-01 | 55.629,24 | 47.287,67 | 8.341,57 | 17,64 |
| 1997-10-01 | 66.749,23 | 55.629,24 | 11.119,98 | 19,99 |
| 1997-11-01 | 43.533,81 | 66.749,23 | -23.215,42 | -34,78 |
| 1997-12-01 | 71.398,43 | 43.533,81 | 27.864,62 | 64,01 |
| 1998-01-01 | 94.222,11 | 71.398,43 | 22.823,68 | 31,97 |
| 1998-02-01 | 99.415,29 | 94.222,11 | 5.193,18 | 5,51 |
| 1998-03-01 | 104.854,16 | 99.415,29 | 5.438,87 | 5,47 |
| 1998-04-01 | 123.798,68 | 104.854,16 | 18.944,53 | 18,07 |
| 1998-05-01 | 18.333,63 | 123.798,68 | -105.465,05 | -85,19 |

**Leitura:** Agosto de 1996 ficou 8,53% abaixo de julho. A maior alta ocorreu em dezembro de 1997 (+64,01%). A queda de 85,19% em maio de 1998 não indica retração: a base só registra pedidos até 06/05/1998.

**Cuidado:** Quando o mês anterior tem valor zero, o percentual fica indefinido. O calendário completo impede que um mês sem vendas seja pulado e que meses não consecutivos sejam comparados.

## 13.10 Q10/P10 — Curva ABC de clientes

**Pergunta:** Como os clientes se distribuem pela curva ABC de valor?

**Cálculo:** Somar valor por cliente, ordenar, calcular acumulado e aplicar os limites de 80% e 95% ao acumulado anterior.

**Recursos:** SQL: CTEs, janela cumulativa e CASE. MongoDB: $lookup, duas janelas e $switch.

**Resultado:** 91 linhas; exibidas as cinco primeiras na ordenação definida.

| cliente (código) | cliente | pedidos | valor | acumulado | classe |
| --- | --- | --- | --- | --- | --- |
| QUICK | QUICK-Stop | 28 | 110.277,31 | 110.277,31 | A |
| ERNSH | Ernst Handel | 30 | 104.874,98 | 215.152,28 | A |
| SAVEA | Save-a-lot Markets | 31 | 104.361,95 | 319.514,23 | A |
| RATTC | Rattlesnake Canyon Grocery | 18 | 51.097,80 | 370.612,03 | A |
| HUNGO | Hungry Owl All-Night Grocers | 19 | 49.979,91 | 420.591,94 | A |

Resumo das 91 linhas por classe:

| classe | clientes | valor | participação (%) |
|---|---|---|---|
| A | 34 | 1.013.547,90 | 80,07 |
| B | 27 | 192.826,66 | 15,23 |
| C | 28 | 59.418,47 | 4,69 |
| sem compras | 2 | 0,00 | 0,00 |

**Leitura:** 34 clientes formam a classe A e concentram 80,07% do valor; 27 ficam na B e 28 na C. QUICK-Stop lidera com 110.277,31. Os dois clientes sem compras ficam fora das classes.

**Cuidado:** A classificação depende da concentração do valor, não da quantidade de clientes; por isso NTILE não seria equivalente. O cliente que cruza um limite permanece na classe que estava sendo completada.

## 13.11 Q11/P11 — RFM descritivo dos clientes

**Pergunta:** Qual é o perfil de recência, frequência e valor de cada cliente?

**Cálculo:** Recência são dias desde a última compra; frequência é quantidade de pedidos; valor é a soma após descontos. Aplicar faixas fixas documentadas.

**Recursos:** SQL: CTE e CASE. MongoDB: $lookup, $dateDiff e condições.

**Resultado:** 91 linhas; exibidas as cinco primeiras na ordenação definida.

| cliente (código) | recência (dias) | frequência | valor | R |
| --- | --- | --- | --- | --- |
| ALFKI | 27 | 6 | 4.273,00 | 3 |
| ANATR | 63 | 4 | 1.402,95 | 2 |
| ANTON | 98 | 7 | 7.023,98 | 1 |
| AROUT | 26 | 13 | 13.390,65 | 3 |
| BERGS | 63 | 18 | 24.927,58 | 2 |

| cliente (código) | F | M |
| --- | --- | --- |
| ALFKI | 2 | 1 |
| ANATR | 1 | 1 |
| ANTON | 2 | 2 |
| AROUT | 3 | 3 |
| BERGS | 3 | 3 |

**Leitura:** 28 clientes têm a combinação máxima R=3, F=3 e M=3: compraram no último mês, fizeram pelo menos dez pedidos e gastaram pelo menos 10.000. Outros 12 compraram recentemente, mas com frequência média e valor baixo (R=3, F=2, M=1), um grupo com espaço para crescer.

**Cuidado:** As faixas são convenções didáticas, não um modelo estatístico. Clientes sem compras recebem escores zero e recência nula, sem data inventada.

## 13.12 Q12/P12 — Produtos comprados juntos

**Pergunta:** Quais produtos aparecem juntos no mesmo pedido?

**Cálculo:** Formar combinações de dois IDs diferentes no pedido, mantendo apenas A menor que B, contar pedidos por par e dividir pelo total de pedidos.

**Recursos:** SQL: Autojunção de itens e agregação. MongoDB: Expansão de arrays, $match e $group.

**Resultado:** 1535 linhas; exibidas as cinco primeiras na ordenação definida.

| produto A | produto B | pedidos | pedidos no período | suporte (%) |
| --- | --- | --- | --- | --- |
| 21 | 61 | 8 | 830 | 0,96 |
| 16 | 31 | 7 | 830 | 0,84 |
| 16 | 60 | 6 | 830 | 0,72 |
| 16 | 62 | 6 | 830 | 0,72 |
| 30 | 54 | 6 | 830 | 0,72 |

**Leitura:** Foram encontrados 1.535 pares diferentes. O mais frequente, produtos 21 e 61, aparece junto em apenas oito pedidos, 0,96% do total. A base não mostra combinações fortes o bastante para sugerir venda casada.

**Cuidado:** Cada par é contado uma vez por pedido, com o menor ID primeiro. O denominador inclui pedidos de um único produto. Frequência conjunta não demonstra efeito causal.

## 13.13 Q13/P13 — Intervalo até envio por transportadora

**Pergunta:** Qual é o intervalo até o envio registrado por transportadora?

**Cálculo:** Subtrair a data do pedido da data de envio onde ela existe; contar ausências separadamente e preservar as transportadoras sem pedidos.

**Recursos:** SQL: Diferença de datas, AVG e FILTER. MongoDB: $lookup, $dateDiff e contagens condicionais.

**Resultado:** 6 linhas; todas exibidas.

| transportadora (ID) | transportadora | pedidos | com data de envio | sem data de envio |
| --- | --- | --- | --- | --- |
| 1 | Speedy Express | 249 | 245 | 4 |
| 2 | United Package | 326 | 315 | 11 |
| 3 | Federal Shipping | 255 | 249 | 6 |
| 4 | Alliance Shippers | 0 | 0 | 0 |
| 5 | UPS | 0 | 0 | 0 |
| 6 | DHL | 0 | 0 | 0 |

| transportadora (ID) | soma de dias | média (dias) | após data requerida |
| --- | --- | --- | --- |
| 1 | 2100 | 8,57 | 12 |
| 2 | 2909 | 9,23 | 16 |
| 3 | 1861 | 7,47 | 9 |
| 4 | 0 | — | 0 |
| 5 | 0 | — | 0 |
| 6 | 0 | — | 0 |

**Leitura:** Speedy Express leva em média 8,57 dias até o envio, sobre 245 envios registrados; quatro de seus 249 pedidos não têm data. No total, há 21 datas ausentes e 37 envios registrados depois da data requerida.

**Cuidado:** O intervalo vai até o envio registrado e não mede a entrega ao cliente. Datas ausentes não entram na média como zero nem provam que o pedido não foi enviado.

## 13.14 Q14/P14 — Descontos sobre o valor dos pedidos

**Pergunta:** Quanto os descontos reduzem o valor bruto dos itens?

**Cálculo:** Somar preço vezes quantidade, somar desconto monetário e subtrair para obter valor após descontos; dividir desconto pelo bruto para a taxa ponderada.

**Recursos:** SQL: Expressões numeric, SUM e razão de somas. MongoDB: Expressões Decimal128, $group e $divide.

**Resultado:** 8 linhas; todas exibidas.

| categoria (ID) | valor bruto | desconto | valor | desconto (%) |
| --- | --- | --- | --- | --- |
| 1 | 286.526,95 | 18.658,77 | 267.868,18 | 6,51 |
| 2 | 113.694,75 | 7.647,67 | 106.047,09 | 6,73 |
| 3 | 177.099,10 | 9.741,88 | 167.357,23 | 5,50 |
| 4 | 251.330,50 | 16.823,22 | 234.507,29 | 6,69 |
| 5 | 100.726,80 | 4.982,21 | 95.744,59 | 4,95 |
| 6 | 178.188,80 | 15.166,44 | 163.022,36 | 8,51 |
| 7 | 105.268,60 | 5.284,02 | 99.984,58 | 5,02 |
| 8 | 141.623,09 | 10.361,35 | 131.261,74 | 7,32 |

**Leitura:** Em Beverages, o desconto soma 18.658,77 sobre bruto de 286.526,95, aproximadamente 6,51%. O cálculo mede redução registrada, sem estimar efeito do desconto sobre a demanda.

**Cuidado:** A taxa é ponderada pelo valor bruto, diferente da média simples das taxas dos itens. Sem custos, o desconto não pode ser convertido em perda de lucro.

## 13.15 Q15/P15 — Vendas próprias e da equipe

**Pergunta:** Quanto foi registrado por cada funcionário e sua equipe?

**Cálculo:** Percorrer os subordinados, incluir o próprio responsável e somar as vendas de cada membro uma vez dentro da equipe.

**Recursos:** SQL: WITH RECURSIVE e pré-agregação. MongoDB: $graphLookup, $setUnion e $lookup.

**Resultado:** 9 linhas; todas exibidas.

| gestor (ID) | membros | valor próprio | pedidos da equipe | valor da equipe |
| --- | --- | --- | --- | --- |
| 1 | 1 | 192.107,60 | 123 | 192.107,60 |
| 2 | 9 | 166.537,76 | 830 | 1.265.793,04 |
| 3 | 1 | 202.812,84 | 127 | 202.812,84 |
| 4 | 1 | 232.890,85 | 156 | 232.890,85 |
| 5 | 4 | 68.792,28 | 224 | 344.581,71 |
| 6 | 1 | 73.913,13 | 67 | 73.913,13 |
| 7 | 1 | 124.568,24 | 72 | 124.568,24 |
| 8 | 1 | 126.862,28 | 104 | 126.862,28 |
| 9 | 1 | 77.308,07 | 43 | 77.308,07 |

**Leitura:** Andrew Fuller (gestor 2) está no topo da hierarquia: sua equipe reúne os nove funcionários e os 830 pedidos. Seu valor próprio é 166.537,76. Steven Buchanan (gestor 5) lidera uma equipe de quatro pessoas, com 344.581,71.

**Cuidado:** As equipes se sobrepõem na hierarquia; somar as linhas de todos os gestores contaria pedidos mais de uma vez. A equipe hierárquica não corresponde à divisão por território.

## 13.16 Q16/P16 — Distribuição trimestral por ano e categoria

**Pergunta:** Como o valor se distribui por ano, trimestre e categoria?

**Cálculo:** Produzir totais trimestrais e sua decomposição por categoria; marcar trimestres cuja cobertura ultrapassa as datas disponíveis.

**Recursos:** SQL: GROUPING SETS e GROUPING. MongoDB: $facet, $concatArrays e agregação temporal.

**Resultado:** 72 linhas; exibidos os oito totais trimestrais.

| ano | trimestre | categoria (ID) | valor | nível | parcial |
| --- | --- | --- | --- | --- | --- |
| 1996 | 3 | — | 79.728,57 | total | sim |
| 1996 | 4 | — | 128.355,40 | total | não |
| 1997 | 1 | — | 138.288,93 | total | não |
| 1997 | 2 | — | 143.177,05 | total | não |
| 1997 | 3 | — | 153.937,77 | total | não |
| 1997 | 4 | — | 181.681,46 | total | não |
| 1998 | 1 | — | 298.491,55 | total | não |
| 1998 | 2 | — | 142.132,31 | total | sim |

**Leitura:** O primeiro trimestre de 1998 foi o maior da série (298.491,55), mais que o dobro do mesmo trimestre de 1997 (138.288,93). O terceiro trimestre de 1996 e o segundo de 1998 têm cobertura parcial.

**Cuidado:** Totais e categorias estão em níveis diferentes e não devem ser somados juntos. Com menos de dois anos completos, a série não permite afirmar sazonalidade recorrente.
