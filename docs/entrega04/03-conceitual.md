# 3. Modelo conceitual

O diagrama mostra as 11 entidades usadas no projeto e como elas se relacionam, sem tipos nem detalhes de armazenamento. ITEM DO PEDIDO e ATUAÇÃO são entidades associativas: a primeira liga pedido e produto; a segunda liga funcionário e território.

<!-- diagram -->

Figura 1 — Entidades e relacionamentos do recorte Northwind, elaborado a partir da base [2]. Os números indicam quantas ocorrências de um lado se relacionam com uma do outro: 1 = exatamente uma; 0..1 = opcional; 0..N = nenhuma ou várias; 1..N = uma ou várias.

<!-- page -->

# 3. Modelo conceitual — regras adotadas

As regras abaixo são decisões do projeto, compatíveis com os dados. Um caso que não aparece na amostra não foi tratado como proibido.

| Relacionamento | Regra |
|---|---|
| Cliente e pedido | Cada pedido tem um cliente; um cliente pode ter zero ou vários pedidos. |
| Funcionário e pedido | Cada pedido tem um funcionário; um funcionário pode não ter pedidos. |
| Transportadora e pedido | Cada pedido indica uma transportadora; ela pode não ter pedidos. |
| Pedido e item | Um pedido tem um ou vários itens; cada item pertence a um pedido. |
| Produto e item | Cada item se refere a um produto; um produto pode não ter sido vendido. |
| Categoria e produto | Cada produto pertence a uma categoria. |
| Fornecedor e produto | Cada produto tem um fornecedor. |
| Região e território | Cada território pertence a uma região. |
| Funcionário e território | Relação N:N, registrada pela atuação. |
| Supervisão | Cada funcionário tem no máximo um superior e pode supervisionar vários. |

ITEM DO PEDIDO é identificado pelo par pedido e produto: o mesmo produto não se repete num pedido, e a quantidade registra quantas unidades foram vendidas. Na amostra, cada um dos 49 territórios com atuação tem um único responsável, mas a relação N:N foi mantida porque o domínio permite mais de um.

A base também tem dois clientes sem pedidos, três transportadoras sem pedidos e quatro territórios sem funcionário. Esses registros foram preservados, porque “não comprou” é uma informação útil. As tabelas demográficas, vazias, e us_states, que não se liga ao restante, ficaram fora do recorte.
