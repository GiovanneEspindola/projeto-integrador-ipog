# 17. Análise de performance e otimização

## 17.1 Método e ambiente

Os 16 pares foram medidos na mesma máquina, sobre os dados validados, com conexões persistentes dos drivers psycopg (PostgreSQL) e PyMongo (MongoDB). Cada medição inclui o envio da consulta, a execução, a transferência e o consumo de **todas** as linhas ou documentos pelo cliente. Abertura de conexão, inicialização de processos, impressão e gravação de arquivos ficaram fora do trecho cronometrado.

O cenário é de **cache aquecido**: cinco execuções de aquecimento e vinte medições por banco e consulta. A ordem entre PostgreSQL e MongoDB alterna a cada rodada. A mediana resume o valor central, e o intervalo entre o primeiro e o terceiro quartil (Q1–Q3) indica a dispersão. Não foram feitos teste de significância estatística nem teste de carga concorrente.

O ambiente executou PostgreSQL 16.15 e MongoDB 7.0.40 em containers Docker, no WSL2, com processador Intel(R) Core(TM) i7-14700HX (28 processadores lógicos visíveis) e 7,8 GB de memória visível no Linux. Os containers não tinham limite de CPU ou memória e compartilharam os recursos da máquina. Configuração relevante do PostgreSQL: effective_cache_size = 4 GB, jit = on, max_parallel_workers_per_gather = 2, shared_buffers = 128 MB, work_mem = 4 MB.

Os planos de execução foram coletados à parte, com EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) e explain("executionStats") [15, 16], para não interferir nos tempos. Custos estimados e tempos internos de um servidor não são comparáveis diretamente com os do outro; a comparação de tempo usa apenas o cronômetro externo comum.

## 17.2 Tempos do catálogo

| Par | PostgreSQL: mediana (ms) | PostgreSQL: Q1–Q3 (ms) | MongoDB: mediana (ms) | MongoDB: Q1–Q3 (ms) |
|---|---|---|---|---|
| 01 | 1,011 | 0,991–1,039 | 2,281 | 2,222–2,304 |
| 02 | 1,391 | 1,321–1,421 | 2,475 | 2,319–2,651 |
| 03 | 0,503 | 0,482–0,533 | 2,846 | 2,774–2,967 |
| 04 | 1,340 | 1,306–1,420 | 3,916 | 3,748–3,966 |
| 05 | 0,218 | 0,213–0,231 | 0,502 | 0,491–0,545 |
| 06 | 0,426 | 0,384–0,469 | 6,312 | 5,879–6,645 |
| 07 | 1,162 | 1,130–1,199 | 2,711 | 2,629–2,787 |
| 08 | 1,380 | 1,326–1,414 | 2,475 | 2,396–2,573 |
| 09 | 1,389 | 1,342–1,455 | 2,520 | 2,416–2,653 |
| 10 | 1,594 | 1,560–1,625 | 6,597 | 6,473–6,842 |
| 11 | 1,504 | 1,457–1,591 | 6,771 | 6,576–7,064 |
| 12 | 2,872 | 2,800–2,960 | 8,242 | 7,925–8,691 |
| 13 | 0,375 | 0,356–0,396 | 2,411 | 2,256–2,462 |
| 14 | 1,441 | 1,419–1,483 | 3,644 | 3,561–3,739 |
| 15 | 1,258 | 1,229–1,292 | 5,706 | 5,605–5,975 |
| 16 | 1,480 | 1,429–1,513 | 4,443 | 4,298–4,567 |

O PostgreSQL apresentou menor mediana nos 16 pares nesta execução; em todos eles, os intervalos Q1–Q3 dos dois bancos não se sobrepõem. O resultado vale para estes códigos, drivers, volume, ambiente e índices. Não demonstra superioridade geral nem indica o comportamento com milhões de pedidos.

Dois fatores de configuração ajudam a interpretar a diferença. Primeiro, os índices não são simétricos: o PostgreSQL tem índices em orders(customer_id), orders(employee_id), orders(order_date) e order_items(product_id), enquanto o MongoDB tem cliente_data, produto_no_pedido e categoria_produto. Sem índice em employee_id e shipper_id, cada $lookup de P04 e P15 examinou os 830 pedidos para cada um dos 9 funcionários (7.470 documentos), e P13 examinou 4.980 documentos para as 6 transportadoras. Segundo, nos pares que partem de cadastros (clientes, funcionários, transportadoras), o pipeline executa uma subconsulta por documento, enquanto o PostgreSQL resolve a junção de uma só vez. Criar índices equivalentes no MongoDB é um teste pendente, não um resultado deste relatório.

<!-- image:apresentacao/evidencias/entrega03/tempos.png -->

Figura 4 — Medianas das 20 medições por par, em milissegundos; as barras de erro indicam Q1 e Q3.

## 17.3 Estudos controlados

Os quatro estudos usam cópias isoladas dos dados. Nas cópias PostgreSQL, foram mantidos apenas os índices de PK e UNIQUE; nas cópias MongoDB, apenas o índice de _id. Para separar o efeito de um índice sem criá-lo ou removê-lo durante as medições, foram mantidas três cópias: sem índices adicionais, com índice em order_date e com índice composto (customer_id, order_date). Os bancos originais não receberam esses índices, e as estatísticas das cópias PostgreSQL foram atualizadas antes das medições.

Em cada estudo, todas as versões foram executadas na mesma sequência de rodadas. A ordem das versões muda a cada rodada, e a ordem dos bancos alterna. Assim, uma variação do ambiente ao longo do tempo não favorece sistematicamente a versão medida primeiro ou por último. Antes das medições, os resultados de todas as versões foram comparados e eram idênticos.

A diferença entre duas versões é considerada consistente nesta execução quando os intervalos Q1–Q3 não se sobrepõem. Isso é uma regra descritiva: não substitui repetição independente nem teste estatístico.

### C01 — Filtro mensal

A versão original obtém o mês com to_char em cada pedido e compara o texto; no MongoDB, cria o campo com $dateToString antes do $match. A reescrita filtra o intervalo de datas diretamente. A terceira versão repete a reescrita na cópia com índice em order_date. As três devolvem o mesmo resultado para janeiro de 1997.

| Versão | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |
|---|---|---|
| original | 0,470 (0,452–0,492) | 1,007 (0,958–1,062) |
| reescrita | 0,364 (0,347–0,385) | 0,684 (0,676–0,731) |
| com_indice | 0,322 (0,310–0,347) | 0,507 (0,488–0,526) |

**Efeito da reescrita do filtro (original → reescrita):** no PostgreSQL, redução de 22,4% na mediana, sem sobreposição dos intervalos Q1–Q3; no MongoDB, redução de 32,1% na mediana, sem sobreposição dos intervalos Q1–Q3.

**Efeito do índice por data (reescrita → com_indice):** no PostgreSQL, redução de 11,5% na mediana, sem sobreposição dos intervalos Q1–Q3; no MongoDB, redução de 25,9% na mediana, sem sobreposição dos intervalos Q1–Q3.

<!-- plano:C01 -->

### C02 — Cliente e período

A mesma consulta — pedidos de VINET em 1996, ordenados por data e ID — foi executada na cópia sem índices adicionais e na cópia com índice composto (customer_id, order_date). O índice já existente no MongoDB original não foi usado como prova: o efeito foi medido nas cópias.

| Versão | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |
|---|---|---|
| sem_composto | 0,199 (0,183–0,206) | 0,644 (0,632–0,664) |
| com_composto | 0,173 (0,160–0,192) | 0,441 (0,429–0,477) |

**Efeito do índice composto (sem_composto → com_composto):** no PostgreSQL, redução de 13,1% na mediana, com sobreposição dos intervalos Q1–Q3, portanto inconclusiva; no MongoDB, redução de 31,5% na mediana, sem sobreposição dos intervalos Q1–Q3.

<!-- plano:C02 -->

### C03 — Pares de produtos

A versão original em SQL foi escrita com uma CTE MATERIALIZED que gera todos os pares de itens de cada pedido antes de aplicar A < B. Sem essa instrução, o PostgreSQL 16 incorporaria a CTE e aplicaria a condição durante a junção, como faz a reescrita (Q12). O estudo mede, portanto, o custo de materializar os pares intermediários, não uma limitação do otimizador. No MongoDB, a versão original mantém todos os campos do pedido e só descarta os pares A ≥ B depois do $group; a reescrita (P12) projeta somente os IDs e filtra antes de agrupar. Nenhum índice mudou.

| Versão | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |
|---|---|---|
| original | 3,353 (3,293–3,443) | 8,300 (8,062–8,710) |
| reescrita | 2,958 (2,871–3,059) | 8,137 (7,921–8,592) |

**Efeito da reescrita (original → reescrita):** no PostgreSQL, redução de 11,8% na mediana, sem sobreposição dos intervalos Q1–Q3; no MongoDB, redução de 2,0% na mediana, com sobreposição dos intervalos Q1–Q3, portanto inconclusiva.

<!-- plano:C03 -->

### C04 — Vendas da equipe

A versão original combina a hierarquia com cada pedido e só depois agrega; a reescrita (Q15) agrega os pedidos por funcionário antes da combinação. No MongoDB, a versão original traz os pedidos completos no $lookup e calcula depois; a reescrita (P15) agrupa dentro do $lookup. Nenhum índice mudou.

| Versão | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |
|---|---|---|
| original | 1,558 (1,470–1,630) | 6,440 (6,095–6,794) |
| reescrita | 1,301 (1,261–1,355) | 5,856 (5,700–6,007) |

**Efeito da reescrita (original → reescrita):** no PostgreSQL, redução de 16,5% na mediana, sem sobreposição dos intervalos Q1–Q3; no MongoDB, redução de 9,1% na mediana, sem sobreposição dos intervalos Q1–Q3.

<!-- plano:C04 -->

## 17.4 Leitura dos planos e limitações

Seq Scan (PostgreSQL) e COLLSCAN (MongoDB) indicam leitura de todas as linhas ou documentos; Index Scan e IXSCAN indicam acesso por índice. No MongoDB, FETCH indica a busca do documento depois da leitura do índice. Em C01, a versão original e a reescrita do PostgreSQL fazem a mesma varredura sequencial, que descarta 797 dos 830 pedidos. A diferença está no custo de converter e formatar a data com to_char em cada linha e na estimativa do otimizador: com to_char ele previu 4 pedidos (foram 33) e escolheu uma agregação com ordenação adicional; com o intervalo, previu 32 e usou agregação por hash. O índice só passa a ser usado na terceira versão. Em C02, o índice composto reduz a leitura a três pedidos nos dois bancos. Em C03 e C04, o objetivo é diminuir os resultados intermediários, não passar a usar índice.

Nos quadros, as linhas examinadas do PostgreSQL somam as linhas descartadas por filtros em todos os nós do plano. No MongoDB, as métricas do cursor inicial e as de cada $lookup são registradas separadamente. Buffers compartilhados indicam acessos a páginas em memória, não necessariamente leituras de disco.

Não foram forçados índices com hint nem desligadas as varreduras sequenciais. Os dados cabem em memória, as consultas são curtas e o tempo medido inclui a comunicação local e a conversão de tipos pelos drivers. O consumo completo pesa mais em Q12/P12, que retorna 1.535 linhas. O estudo não mede concorrência, custo de escrita, sincronização entre os bancos nem escalabilidade.
