# 5. Abordagem híbrida

O fluxo implementado é **PostgreSQL public → PostgreSQL nw → MongoDB**. A fonte original permanece preservada. O schema nw aplica as decisões relacionais; o MongoDB recebeu uma cópia para consultas, carregada por um processo em lote. A atualização documental foi definida em um único sentido, tendo o modelo relacional como origem.

## 5.1 Organização do MongoDB

| Coleção | Organização implementada |
|---|---|
| orders | Um documento por pedido, com itens embutidos, datas, frete, endereço de envio e identificadores de cliente, funcionário e transportadora. Nos itens: produto, categoria, quantidade, preço praticado e desconto. |
| products | Produto com estoque, categoria e fornecedor identificados; nomes selecionados foram copiados para facilitar a leitura. |
| customers | Cadastro do cliente com endereço agrupado em um objeto. |
| employees | Cadastro do funcionário, referência ao superior e lista de territórios de atuação. |
| categories, suppliers e shippers | Cadastros completos para preservar também registros sem pedido ou produto associado. |
| territories e regions | Cadastros completos, incluindo territórios sem funcionário vinculado. |

Foram implementadas **nove coleções**. Os 830 pedidos e seus 2.155 itens formam 830 documentos em orders. O critério de agrupamento segue a orientação de considerar o acesso aos dados ao decidir entre incorporação e referências [5].

## 5.2 Carga e validação

O processo usa identificadores estáveis e substituição por identificador, evitando duplicações ao repetir a carga. Registros removidos da origem provocam interrupção para revisão antes da gravação; não há exclusão automática. Valores monetários são convertidos de **numeric para Decimal128**, sem passar por float; datas e nulos seguem uma convenção única [6].

Os dados copiados de cadastros representam o estado disponível na extração, sem serem apresentados como histórico da data da venda. O preço praticado e o endereço de envio vêm do próprio pedido. A duplicação de nomes e categorias exige atualização das cópias quando a fonte mudar.

A validação compara identificadores, contagens, quantidade de itens por pedido e valores calculados com a mesma regra. Foram definidos validadores de estrutura e índices conforme as consultas. Referências entre coleções são conferidas após a carga; a validação de documentos não substitui as chaves estrangeiras relacionais [7].

## 5.3 Comparação prevista e estado atual

A hipótese é que incorporar itens simplifique a leitura de um pedido completo, enquanto consultas que cruzam cadastros possam exigir referências e agregações adicionais. O resultado de desempenho está em aberto. A medição usará consultas equivalentes, mesma máquina, recursos registrados, aquecimento e pelo menos dez repetições, com mediana e dispersão dos tempos.

O MongoDB está carregado com **1.107 documentos**. Seu modo atual é **standalone**, sem transações entre vários documentos; a escrita em um único documento é atômica [5, 8]. A transformação SQL, a carga mongosh, os validadores e os índices são detalhados nas seções seguintes. As consultas analíticas equivalentes permanecem para as próximas etapas. O volume pequeno não permite concluir sobre escalabilidade.
