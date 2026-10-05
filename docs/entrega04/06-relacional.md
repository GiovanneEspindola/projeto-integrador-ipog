# 6. Modelo relacional

O schema **nw** tem 11 tabelas e 3.311 linhas. As duas tabelas demográficas vazias e us_states ficaram apenas na fonte. Em relação à base original, o modelo corrige tipos e acrescenta regras:

| Item | Implementação |
|---|---|
| Chaves | 11 chaves primárias e 11 chaves estrangeiras |
| Regras de domínio | 17 restrições CHECK (valores não negativos, desconto de 0 a menos de 1, quantidade positiva, envio não anterior ao pedido, entre outras) |
| Unicidade | 4 restrições UNIQUE, como nome de categoria e produto por fornecedor |
| Tipos | Dinheiro em numeric(10,2), desconto em numeric(4,3), discontinued como boolean |
| Índices | orders(customer_id), orders(employee_id), orders(order_date) e order_items(product_id) |

## 6.1 Normalização

Os itens ficam numa tabela própria, order_items, com chave (order_id, product_id). Isso evita colunas repetidas como produto_1 e produto_2 e permite qualquer número de itens por pedido (primeira forma normal).

O preço do item depende da venda, não só do produto: o mesmo produto foi vendido a preços diferentes em pedidos diferentes. Por isso unit_price fica em order_items, e não é buscado em products. O mesmo raciocínio mantém o endereço de envio em orders. Já o nome do cliente depende apenas do cliente e fica só em customers, sem cópias nos pedidos.

O campo quantity_per_unit (por exemplo, “10 boxes x 30 bags”) foi mantido como texto descritivo, porque o projeto não precisa separar quantidade e embalagem.

## 6.2 Modelo lógico

<!-- image:docs/diagramas/er-logico.png -->

Figura 3 — Modelo lógico do schema nw, com tipos e chaves.

As chaves estrangeiras garantem que um item aponte para um pedido existente, mas não garantem que todo pedido tenha ao menos um item. Essa regra foi verificada por consulta (capítulo 4). Os índices foram escolhidos pelos acessos mais frequentes das análises: pedidos por cliente, por funcionário e por data, e itens por produto.
