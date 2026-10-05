| Par | SQL: recursos | Linhas SQL | MongoDB: recursos | Estágios |
|---|---|---|---|---|
| 01 | JOIN, GROUP BY e SUM OVER | 8 | $unwind, $group e $setWindowFields | 6 |
| 02 | CTEs, generate_series e agregação em dois níveis | 10 | $map, $group, $facet e calendário por $dateAdd | 8 |
| 03 | NOT EXISTS e junções cadastrais | 7 | $lookup com $limit e filtro de array vazio | 4 |
| 04 | LEFT JOIN, agregação e janela global | 10 | $lookup, $group e $setWindowFields | 5 |
| 05 | Comparação entre colunas, FILTER e array_agg | 7 | $expr, $set, $group e $push | 6 |
| 06 | LEFT JOIN, MAX e comparação de datas | 9 | $lookup, $dateDiff e tratamento de null | 5 |
| 07 | ROW_NUMBER com PARTITION BY | 7 | $setWindowFields e soma cumulativa de 1 | 7 |
| 08 | SUM OVER com ROWS UNBOUNDED PRECEDING | 10 | $setWindowFields com janela até current | 9 |
| 09 | LAG e NULLIF | 13 | $shift e $cond | 10 |
| 10 | CTEs, janela cumulativa e CASE | 13 | $lookup, duas janelas e $switch | 5 |
| 11 | CTE e CASE | 11 | $lookup, $dateDiff e condições | 5 |
| 12 | Autojunção de itens e agregação | 8 | Expansão de arrays, $match e $group | 6 |
| 13 | Diferença de datas, AVG e FILTER | 7 | $lookup, $dateDiff e contagens condicionais | 4 |
| 14 | Expressões numeric, SUM e razão de somas | 4 | Expressões Decimal128, $group e $divide | 6 |
| 15 | WITH RECURSIVE e pré-agregação | 15 | $graphLookup, $setUnion e $lookup | 5 |
| 16 | GROUPING SETS e GROUPING | 11 | $facet, $concatArrays e agregação temporal | 11 |
