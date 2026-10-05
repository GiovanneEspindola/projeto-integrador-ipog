# 6. Critérios para a modelagem documental

A exploração identificou uma base com 830 pedidos, 2.155 itens, 91 clientes e 77 produtos. Os pedidos cobrem parte de 1996, todo o ano de 1997 e parte de 1998. Seus valores apresentam concentração em determinadas categorias e diferença entre média e mediana, o que orienta o aprofundamento das análises comerciais.

As verificações de identificadores, referências e faixas de valores não apontaram inconsistências nas regras examinadas. As principais limitações são as datas de envio ausentes, a falta de custos e pagamentos, os anos parciais e o uso de tipos aproximados na fonte. Esses achados fundamentaram os critérios adotados na transformação dos dados.

## 6.1 Preservação das informações da venda

Os preços praticados e os endereços de envio foram mantidos como atributos próprios dos pedidos. A diferença entre o preço do item e o preço de catálogo em 662 itens mostrou que o cadastro atual não poderia substituir a informação da venda. Da mesma forma, as diferenças de endereço em 82 pedidos justificaram conservar o endereço de envio integralmente.

Os dados ausentes permaneceram nulos. A ausência de data de envio, por exemplo, não foi convertida em uma data estimada nem interpretada como comprovação de que o pedido nunca foi enviado. Os cadastros sem movimento também foram preservados, permitindo distinguir ausência de compra registrada de ausência do cliente na base.

## 6.2 Consistência dos indicadores

O cálculo dos valores manteve o preço praticado no item, a quantidade e o desconto, com arredondamento somente após a soma. A conversão para tipos decimais evitou introduzir novas aproximações de ponto flutuante na transformação, respeitando a precisão disponível na origem.

A conferência do modelo documental foi orientada pela comparação de identificadores e conteúdo, além das contagens. Esse critério permite verificar se a reorganização das linhas em objetos e arrays preservou as informações utilizadas nos indicadores. A igualdade de contagens, isoladamente, não comprovaria a manutenção de preços, descontos, datas ou endereços.

As regras de qualidade da base foram consideradas na definição dos validadores e na conferência das referências. A análise das consultas e do desempenho depende dessa consistência: diferenças decorrentes de arredondamento ou de perda de dados não devem ser interpretadas como características dos modelos de armazenamento.
