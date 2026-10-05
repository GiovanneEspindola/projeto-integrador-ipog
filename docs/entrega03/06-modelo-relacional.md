# 6. Implementação relacional e decisões de modelagem

O schema **public** conserva a fonte com 14 tabelas. O schema **nw** representa o recorte implementado, com 11 tabelas e 3.311 linhas. Duas tabelas vazias de segmentação demográfica e a tabela us_states permanecem somente na fonte, pois não participam das análises. Essa separação permite verificar as alterações de tipos, estrutura e regras.

A implementação inclui 11 chaves primárias, 11 chaves estrangeiras, 17 restrições CHECK e quatro restrições UNIQUE. Os valores monetários usam numeric(10,2), descontos usam numeric(4,3) e discontinued é booleano. A chave de order_items é (order_id, product_id): a quantidade representa as unidades do produto naquele pedido.

As regras verificam, entre outros aspectos, valores não negativos, descontos menores que um e coerência das datas. Chaves estrangeiras garantem a existência das referências; não garantem, sozinhas, que todo pedido tenha ao menos um item. Essa participação mínima é verificada separadamente.

## 6.1 Normalização e preservação da venda

Os itens ficam em uma relação própria, evitando colunas repetidas como produto_1 e produto_2. O preço praticado depende do item daquela venda, não apenas do produto: usar o preço atual do cadastro alteraria o histórico. A exploração identificou 662 itens cujo preço difere do catálogo.

O cadastro do cliente fica separado dos pedidos. O endereço de envio permanece no pedido porque é uma informação daquela operação: 82 pedidos divergem do cadastro em pelo menos um dos seis campos comparados. Não se deve substituir esse endereço pelo atual.

O campo quantity_per_unit permanece como descrição da embalagem. Sua atomicidade depende do domínio adotado: tratado como descrição textual, ele é um atributo único; analisar separadamente quantidade, embalagem e unidade exigiria modelagem e transformação adicionais. Não se afirma BCNF para todas as tabelas apenas pela ausência de anomalias na amostra. Dependências funcionais precisam corresponder às regras do domínio.

## 6.2 Modelo lógico e índices

O diagrama lógico abaixo documenta tabelas, colunas, tipos e relações do schema nw. A consulta analítica acrescenta views em outro schema, sem mudar essas entidades.

<!-- image:docs/diagramas/er-logico.png -->

Figura 2 — Modelo lógico relacional de nw, mantido no projeto.

Existem quatro índices adicionais voltados aos acessos em orders(customer_id), orders(employee_id), orders(order_date) e order_items(product_id). PKs e restrições UNIQUE também criam índices. As decisões anteriores permanecem contextualizadas ao volume da base; na Entrega 3, novos índices foram avaliados em cópias isoladas e não aplicados automaticamente ao banco original.

A escolha de um índice no plano depende da consulta, seletividade, estatísticas e volume. Uma varredura sequencial pode ser adequada numa tabela pequena. O relatório de performance apresenta os casos medidos e evita tratar a presença de índice como garantia de melhora.
