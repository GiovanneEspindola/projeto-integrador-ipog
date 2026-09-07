# 5. Plano de implementação híbrida

O fluxo proposto é **PostgreSQL public → PostgreSQL nw → MongoDB**. A fonte original permanece preservada. O schema nw aplica as decisões relacionais; o MongoDB receberá uma cópia para consultas, carregada por um processo em lote. Não haverá sincronização nos dois sentidos nesta implementação didática.

## 5.1 Organização prevista no MongoDB

| Coleção | Organização planejada |
|---|---|
| orders | Um documento por pedido, com itens embutidos, datas, frete, endereço de envio e identificadores de cliente, funcionário e transportadora. Nos itens: produto, categoria, quantidade, preço praticado e desconto. |
| products | Produto com estoque, categoria e fornecedor identificados; nomes selecionados poderão ser copiados para facilitar a leitura. |
| customers | Cadastro do cliente com endereço agrupado em um objeto. |
| employees | Cadastro do funcionário, referência ao superior e lista de territórios de atuação. |
| categories, suppliers e shippers | Cadastros completos para preservar também registros sem pedido ou produto associado. |
| territories e regions | Cadastros completos, incluindo territórios sem funcionário vinculado. |

São previstas **nove coleções**. Com o conjunto atual, os 830 pedidos e seus 2.155 itens formarão 830 documentos em orders. O critério de agrupamento segue a orientação de considerar o acesso aos dados ao decidir entre incorporação e referências [5].

## 5.2 Carga e validação

O processo usará identificadores estáveis e substituição por identificador, evitando duplicações ao repetir a carga. A estratégia também deverá tratar registros removidos da origem. Valores monetários serão convertidos de **numeric para Decimal128**, sem passar por float; datas e nulos seguirão uma convenção única [6].

Os dados copiados de cadastros representarão o estado disponível na extração, sem serem apresentados como histórico da data da venda. O preço praticado e o endereço de envio virão do próprio pedido. A duplicação de nomes e categorias exigirá atualização das cópias quando a fonte mudar.

A validação comparará identificadores, contagens, quantidade de itens por pedido e valores calculados com a mesma regra. Serão definidos validadores de estrutura e índices conforme as consultas. Referências entre coleções precisarão de conferência no processo de carga; a validação de documentos não substitui as chaves estrangeiras relacionais [7].

## 5.3 Comparação prevista e estado atual

A hipótese é que incorporar itens simplifique a leitura de um pedido completo, enquanto consultas que cruzam cadastros possam exigir referências e agregações adicionais. O resultado de desempenho está em aberto. A medição usará consultas equivalentes, mesma máquina, recursos registrados, aquecimento e pelo menos dez repetições, com mediana e dispersão dos tempos.

A implementação relacional já foi iniciada; o MongoDB ainda está vazio. Seu modo atual é **standalone**, sem transações entre vários documentos; a escrita em um único documento é atômica [5, 8]. O ETL, os validadores e as consultas equivalentes serão implementados nas próximas entregas. O volume pequeno não permite concluir sobre escalabilidade.
