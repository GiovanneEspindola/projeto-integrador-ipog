# 2. Compreensão do negócio

A empresa vende produtos de várias categorias, comprados de fornecedores cadastrados. Os clientes fazem pedidos, registrados por funcionários. Cada pedido tem um ou mais itens, com produto, quantidade, preço praticado e desconto, e indica uma transportadora. Os funcionários formam uma hierarquia e atuam em territórios agrupados em regiões.

A base cobre o pedido até o envio. Ela não registra pagamento, entrega ao cliente, devoluções nem custo dos produtos. Isso define o que o projeto pode e o que não pode afirmar.

## 2.1 Perguntas de negócio

| Pergunta | Para que serve |
|---|---|
| Quais categorias e produtos concentram o valor dos pedidos? | Saber de onde vem a receita registrada. |
| Como variam o volume e o valor médio dos pedidos ao longo dos meses? | Acompanhar a evolução comercial. |
| Quais clientes compram mais e quais pararam de comprar? | Orientar ações de relacionamento. |
| Quanto foi registrado por vendedor e por equipe? | Descrever a distribuição das vendas. |
| Quais produtos estão abaixo do ponto de reposição? | Sinalizar riscos no estoque cadastrado. |
| Quanto tempo leva do pedido ao envio, por transportadora? | Observar a operação de envio. |

Essas seis perguntas foram desdobradas nas 16 análises do capítulo 13.

## 2.2 Definições usadas em todo o relatório

**Valor do pedido:** soma de preço praticado × quantidade × (1 − desconto) de seus itens, sem frete. É o valor registrado, não o valor recebido. A base não identifica a moeda, então os valores aparecem em unidades monetárias.

**Ticket médio:** valor total dividido pelo número de pedidos. Os itens são somados por pedido antes da média, para que um pedido com cinco itens conte uma vez, e não cinco.

**Recência:** dias desde a última compra, contados a partir de 06/05/1998, data do último pedido da base. Usar a data de hoje tornaria todos os clientes igualmente antigos.

**O que fica de fora:** sem custos, não há margem nem lucro; sem pagamentos, não há receita recebida; sem data de chegada, não há prazo de entrega. As tabelas demográficas estão vazias, então a segmentação de clientes usa apenas o histórico de compras.
