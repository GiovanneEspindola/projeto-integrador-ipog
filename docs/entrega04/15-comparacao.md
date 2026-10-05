# 15. Comparação de sintaxe e complexidade

SQL descreve o resultado desejado: quais tabelas juntar, como agrupar, o que filtrar. Um pipeline descreve uma sequência de etapas pelas quais os documentos passam. Nos dois casos, um otimizador decide a execução, e a ordem escrita não é necessariamente a ordem executada.

A tabela resume os recursos de cada par. As linhas de SQL (sem comentários) e os estágios do pipeline (sem contar os internos de $lookup e $facet) indicam tamanho, não dificuldade.

<!-- comparacao -->

## 15.1 Onde cada modelo foi mais natural

**O documento ajudou quando a pergunta é sobre o pedido.** Valor por pedido, ticket mensal e pares de produtos usam os itens que já estão dentro do documento: basta $map ou $unwind, sem junção.

**O SQL foi mais direto quando a pergunta parte de um cadastro ou cruza entidades.** Clientes sem compra, vendas por funcionário e por transportadora começam por uma coleção de cadastro e precisam de $lookup para chegar aos pedidos. Em SQL, é um LEFT JOIN. A hierarquia de funcionários usa WITH RECURSIVE no PostgreSQL e $graphLookup no MongoDB, com tamanho parecido.

**Ranking e janelas existem nos dois.** ROW_NUMBER e SUM OVER têm equivalente em $setWindowFields. Houve uma diferença prática: no MongoDB 7, $documentNumber aceita um único campo de ordenação [8], então o ranking com desempate por ID foi feito com uma soma acumulada de 1.

**Montar um calendário completo é mais longo no MongoDB.** No SQL, generate_series cria os 23 meses e um LEFT JOIN preenche os vazios. No pipeline, foi preciso gerar a lista com $range e $dateAdd e procurar cada mês com $filter. Por isso P02, P08 e P09 estão entre os pipelines com mais estágios.

Em resumo: a incorporação dos itens simplificou as consultas centradas no pedido, mas não eliminou as junções. Elas apenas mudaram de lugar.
