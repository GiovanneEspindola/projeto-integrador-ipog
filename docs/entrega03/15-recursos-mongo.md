# 15. Recursos documentais e MapReduce

## 15.1 Arrays, redução e múltiplas saídas

A primeira demonstração seleciona pedidos que tenham o produto 11, quantidade de pelo menos dez e desconto positivo no **mesmo item**, usando $elemMatch. $filter apresenta somente os itens correspondentes. Condições independentes sobre um array poderiam ser satisfeitas por itens diferentes, produzindo uma interpretação incorreta.

A segunda demonstração mantém um documento por pedido e calcula seu valor por $reduce, enquanto $map extrai os nomes dos produtos. Para o pedido 10248, os itens totalizam 440,00. Não é necessário expandir os itens em várias linhas para responder a essa pergunta.

A terceira usa $facet para devolver volume, presença de data de envio e distribuição da quantidade de itens dos pedidos de 1997. Cada faceta responde a uma pergunta sobre o mesmo recorte. A utilidade do formato não implica vantagem de desempenho em qualquer cenário.

<!-- recursos -->

## 15.2 MapReduce e equivalente moderno

A análise MapReduce soma as quantidades vendidas por produto. A função map emite o ID e a quantidade de cada item; reduce soma os valores de cada produto. O resultado foi comparado ao pipeline com $unwind e $group: **77 produtos, 51.317 unidades e igualdade de todos os totais**. A saída foi retornada em memória, sem criar coleção de resultados.

Essa demonstração usa quantidades inteiras, evitando conversões monetárias para números JavaScript. MapReduce está depreciado desde MongoDB 5.0; a documentação recomenda aggregation pipelines para novos desenvolvimentos [14]. O recurso foi executado para atender à atividade da disciplina e contextualizado como abordagem legada.

O código completo das três demonstrações e do MapReduce, incluindo sua comparação automática com o pipeline, está no Apêndice B.
