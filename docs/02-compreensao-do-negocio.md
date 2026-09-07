# 2. Compreensão do negócio

A empresa comercializa produtos de diferentes categorias, fornecidos por empresas cadastradas. Os clientes fazem pedidos registrados por funcionários. Cada pedido reúne um ou mais itens, com produto, quantidade, preço praticado e desconto. Uma transportadora é indicada no pedido. A equipe comercial também está vinculada a territórios agrupados em regiões.

A base representa o cadastro comercial, os pedidos e informações de envio. Ela não registra o recebimento de pagamento nem a confirmação de entrega ao cliente. Assim, o processo observado vai do registro do pedido às informações disponíveis sobre seu envio.

## 2.1 Informações que se pretende obter

| Pergunta de negócio | Uso da informação |
|---|---|
| Quais categorias e produtos concentram o valor dos pedidos? | Identificar a participação de cada parte do catálogo. |
| Como variam o volume e o valor médio dos pedidos ao longo dos meses? | Acompanhar a evolução comercial dentro do período disponível. |
| Quais clientes compram mais e quais estão sem compras recentes? | Apoiar ações de relacionamento com clientes. |
| Quanto foi registrado por vendedor e por equipe? | Descrever a distribuição das vendas entre os responsáveis. |
| Quais produtos estão abaixo do ponto de reposição? | Identificar sinais de atenção no estoque cadastrado. |
| Qual é o intervalo entre o pedido e o envio por transportadora? | Examinar o tempo até o envio registrado, sem confundi-lo com prazo de entrega. |

Essas perguntas orientam o detalhamento das consultas nas próximas etapas. Nesta entrega, a exploração já verifica o período, o volume, a distribuição dos valores e a participação das categorias.

## 2.2 Definições para interpretar os resultados

**Valor do item:** preço praticado no item × quantidade × (1 − desconto). O valor de um pedido é a soma de seus itens. Neste relatório, “valor dos pedidos” é o total após descontos, sem acrescentar frete. Ele não comprova recebimento financeiro. Os valores são apresentados em unidades monetárias da base, sem atribuir uma moeda que não está identificada nas tabelas analisadas.

**Ticket médio:** soma do valor dos pedidos dividida pelo número de pedidos. O cálculo agrupa os itens antes de calcular a média, para não tratar cada item como um pedido independente.

**Recência:** as análises futuras usarão como referência o último dia com pedido, 06/05/1998. Usar a data atual tornaria todos os clientes antigos e não ajudaria a distinguir seu comportamento no recorte.

**Limites do negócio:** não há custo de aquisição para calcular margem ou lucro, nem registros de pagamentos, devoluções ou cancelamentos. A ausência dessas tabelas não comprova que esses eventos nunca ocorreram. A segmentação demográfica não é viável com as tabelas vazias, mas a segmentação por recência, frequência e valor das compras continua possível.
