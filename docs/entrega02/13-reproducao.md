# 11. Conclusões e continuidade

A modelagem documental representou os dados relacionais do Northwind em nove coleções, com 1.107 documentos. A incorporação dos itens e do endereço de envio permitiu reunir os dados de cada pedido em uma única estrutura. Os cadastros permaneceram em coleções próprias, mantendo as referências necessárias e os registros sem movimento.

A transformação preservou os identificadores, os campos nulos, as datas, os preços praticados, os descontos e os endereços dos pedidos. A conferência independente reconstruiu as 3.311 linhas de nw sem divergências. A repetição da carga não inseriu nem modificou documentos, confirmando que o mesmo conjunto de dados pode ser carregado novamente sem duplicação.

## 11.1 Avaliação do modelo

O pedido 10248 exemplifica a organização adotada: seus três itens, antes armazenados em linhas separadas, passaram a integrar um array no documento. Produto e categoria foram representados em objetos aninhados, permitindo identificar os itens sem consultar outros cadastros para obter seus nomes. O custo dessa escolha é a manutenção das informações copiadas quando os cadastros mudam.

Os validadores rejeitaram as cinco alterações inválidas testadas e preservaram o documento original. A existência das referências e a coerência entre documentos foram verificadas separadamente, pois a estrutura documental não oferece as mesmas garantias das chaves estrangeiras relacionais.

Os índices foram definidos para pedidos por cliente e período, pedidos por produto e produtos por categoria. Na consulta observada para o cliente VINET em 1996, o MongoDB utilizou o índice composto e examinou três documentos para retornar três pedidos. Esse resultado sustenta a escolha do índice para o acesso avaliado.

## 11.2 Limitações e continuidade

Os resultados comprovam a preservação dos dados no conjunto analisado, mas não permitem concluir sobre escalabilidade ou superioridade de desempenho entre os bancos. O volume é pequeno, e as medições de tempo de consultas equivalentes ainda não foram realizadas.

A carga em lote depende de nova extração para refletir mudanças na origem. As cópias de nomes e categorias representam o estado cadastral disponível na extração, sem reconstruir seu histórico na data da venda. O modo standalone também limita a atomicidade ao documento, exigindo nova conferência após a recuperação de uma carga interrompida.

A continuidade do trabalho consiste na implementação de consultas analíticas equivalentes e na avaliação de desempenho, mantendo as definições dos indicadores, o preço praticado no item e os critérios de precisão. A equivalência já verificada fornece uma base consistente para comparar os dois modelos sem atribuir a diferenças de tecnologia resultados causados por perda ou alteração de dados.
