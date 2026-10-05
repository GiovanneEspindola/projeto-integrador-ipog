# 18. Escalabilidade e manutenção

Este capítulo é uma análise argumentada. Com 830 pedidos, todos os dados cabem em memória, e nenhum teste de grande volume, concorrência ou distribuição foi feito. As medições do capítulo 16 não devem ser projetadas para milhões de pedidos.

## 18.1 Como cada modelo cresceria

| Aspecto | PostgreSQL | MongoDB |
|---|---|---|
| Crescimento principal | Vertical (servidor maior) e réplicas de leitura | Horizontal, distribuindo coleções entre servidores (sharding) |
| Tabela ou coleção que mais cresce | orders e order_items; candidatas a particionamento por data | orders; a chave de distribuição precisaria seguir o acesso, como customer_id |
| Ponto de atenção | Junções sobre tabelas grandes dependem de índices e estatísticas | $lookup entre coleções distribuídas fica mais caro; o modelo precisa evitar junções nas consultas frequentes |
| Tamanho do documento | Não se aplica | Há um limite por documento; um pedido com dezenas de itens fica muito longe dele, mas um cliente com todos os seus pedidos dentro não ficaria |

O próprio projeto deu um sinal do que acontece com volume maior. Sem índice em employee_id, cada $lookup por funcionário examinou os 830 pedidos (7.470 documentos no total). Com o índice, foram 830. A diferença de tempo hoje é de cerca de 1 milissegundo; com milhões de pedidos, a mesma falta de índice faria a consulta varrer a coleção inteira para cada funcionário.

## 18.2 Custos de manutenção observados

**Mudanças de cadastro.** No PostgreSQL, renomear um produto altera uma linha. No MongoDB, o nome está copiado em todos os itens daquele produto, em todos os pedidos, e precisa ser atualizado também.

**Mudanças de estrutura.** Acrescentar um campo é mais simples no MongoDB, porque documentos antigos e novos convivem. Em compensação, o validador e as consultas precisam acompanhar a mudança, ou a flexibilidade vira inconsistência.

**Índices.** Nos dois bancos, índices precisam ser revistos conforme as consultas mudam. O teste da Entrega 4 mostrou que dois índices esquecidos explicavam até 27% do tempo de algumas consultas no MongoDB.

**Dois bancos em operação.** A arquitetura híbrida dobra backups, monitoramento e atualizações, e acrescenta a extração, que precisa ser executada e conferida sempre que a fonte mudar. A conferência automática construída aqui (reconstrução das 3.311 linhas) é o que torna essa manutenção segura.

## 18.3 Custo e benefício das decisões técnicas

| Decisão | Custo | Benefício |
|---|---|---|
| Decimais exatos e arredondamento só no fim | Cuidado em cada cálculo | Totais idênticos nos dois bancos; evitou a diferença de 0,25 |
| Schema próprio (nw) separado da fonte | Um script de carga a mais | Regras de domínio no banco e a fonte preservada para comparação |
| Itens incorporados no pedido | Cópias de nome e categoria a manter | Pedido lido sem junção; consultas de pedido mais simples |
| Conferência em três caminhos | Tempo de desenvolvimento | Confiança de que SQL e MongoDB não erraram juntos |
| Arquitetura híbrida | Dois bancos e uma extração | Comparação justa; pronta para uma camada de leitura, se necessária |
