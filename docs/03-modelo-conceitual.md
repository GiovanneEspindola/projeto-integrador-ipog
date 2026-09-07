# 3. Modelo conceitual

O diagrama apresenta 11 entidades do recorte de vendas. Os identificadores descrevem como cada entidade é reconhecida; tipos SQL, índices e detalhes de armazenamento ficam para o modelo lógico e físico. ITEM DO PEDIDO e ATUAÇÃO são entidades associativas.

<!-- diagram -->

Figura 1 — Entidades e relacionamentos do recorte Northwind. Elaboração própria a partir da base [2]. Os números próximos a cada entidade indicam quantas ocorrências daquele lado podem se relacionar com uma ocorrência do outro lado: 1 = exatamente uma; 0..1 = opcional; 0..N = nenhuma ou várias; 1..N = uma ou várias.

<!-- page -->

# 3. Modelo conceitual — regras adotadas

As regras abaixo são escolhas para este projeto, compatíveis com os dados observados. A ausência de um caso na amostra não significa que ele deva ser proibido no modelo.

| Relacionamento | Regra adotada |
|---|---|
| Cliente e pedido | Cada pedido tem um cliente. Um cliente pode ter zero ou vários pedidos. |
| Funcionário e pedido | Cada pedido tem um funcionário responsável. Um funcionário pode não ter pedidos. |
| Transportadora e pedido | Cada pedido tem uma transportadora indicada. Ela pode não aparecer em nenhum pedido. |
| Pedido e item | Um pedido tem um ou vários itens. Cada item pertence a um único pedido. |
| Produto e item | Cada item se refere a um produto. Um produto pode não aparecer em pedidos. |
| Categoria e produto | Cada produto pertence a uma categoria. A categoria pode não ter produtos. |
| Fornecedor e produto | Cada produto tem um fornecedor cadastrado. O fornecedor pode não ter produtos. |
| Região e território | Cada território pertence a uma região. Neste recorte, uma região reúne um ou vários territórios. |
| Funcionário, atuação e território | Cada atuação vincula um funcionário a um território. Ambos podem ter zero ou vários vínculos. |
| Supervisão de funcionários | Um funcionário tem no máximo um superior e pode supervisionar vários funcionários. |

## 3.1 Identificação e participação

ITEM DO PEDIDO é identificado pelo par **pedido e produto**. O modelo não permite repetir esse par; a quantidade registra quantas unidades foram incluídas. ATUAÇÃO é identificada pelo par **funcionário e território**, permitindo representar vários responsáveis por um território quando necessário.

Na amostra, os 49 vínculos de atuação abrangem 49 territórios distintos: nenhum tem dois responsáveis registrados. A estrutura N:N é mantida como possibilidade do modelo. Também existem dois clientes sem pedidos, três transportadoras sem pedidos e quatro territórios sem funcionário vinculado.

As ligações de pedido com cliente, funcionário e transportadora, e de produto com categoria e fornecedor, aceitam nulos na fonte, embora não apresentem nulos na amostra. Sua obrigatoriedade é uma regra adotada no modelo do projeto. Já a exigência de ao menos um item por pedido precisa de validação adicional: uma chave estrangeira, sozinha, não garante que o pedido tenha itens.

## 3.2 Recorte do modelo

As tabelas **customer_demographics** e **customer_customer_demo** estão vazias e não serão usadas nas análises previstas. **us_states** tem 51 registros, mas não participa das relações utilizadas. As três permanecem preservadas na fonte. Sua exclusão se deve ao escopo; uma entidade pode ser válida mesmo sem registros.
