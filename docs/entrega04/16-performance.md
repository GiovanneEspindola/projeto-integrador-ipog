# 16. Performance e otimização

## 16.1 Como foi medido

As 16 consultas e os 16 pipelines rodaram na mesma máquina, sobre os mesmos dados, por conexões já abertas (psycopg e PyMongo). O tempo vai do envio da consulta até o consumo de **todas** as linhas pelo programa. Cada par teve cinco execuções de aquecimento e vinte medições, alternando qual banco rodava primeiro. O relatório usa a **mediana** e o intervalo entre o primeiro e o terceiro quartil (Q1–Q3), que mostra a variação entre as medições.

Ambiente: PostgreSQL 16.15 e MongoDB 7.0.40 em Docker, no WSL2, processador Intel(R) Core(TM) i7-14700HX e 7,8 GB de memória, sem limite de CPU ou memória para os containers. Os planos de execução (EXPLAIN e explain) foram coletados à parte, para não interferir nos tempos.

## 16.2 Tempos das 16 análises

| Par | PostgreSQL: mediana (ms) | PostgreSQL: Q1–Q3 | MongoDB: mediana (ms) | MongoDB: Q1–Q3 |
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

O PostgreSQL teve a menor mediana nos 16 pares, com o MongoDB entre 1,8 e 14,8 vezes mais lento. Os intervalos Q1–Q3 não se sobrepõem em nenhum par, então a diferença é consistente nesta execução. Ela vale para este volume, esta máquina e estes índices.

<!-- image:apresentacao/evidencias/entrega04/tempos.png -->

Figura 5 — Mediana das 20 medições por par, em milissegundos; as barras indicam Q1 e Q3.

As maiores diferenças relativas estão em P06 (14,8×), P13 (6,4×), P03 (5,7×), P15 (4,5×), P11 (4,5×), P10 (4,1×). Todos esses pipelines começam por um cadastro (produtos, clientes, funcionários ou transportadoras) e fazem um $lookup nos pedidos para cada documento, enquanto o PostgreSQL resolve a junção de uma vez. Os planos mostraram ainda que o MongoDB não tinha índice em employee_id nem em shipper_id: cada $lookup de P04 e P15 examinava os 830 pedidos.

## 16.3 Teste da Entrega 4: os índices que faltavam

Para saber quanto da diferença vinha dos índices ausentes, os três pipelines afetados foram medidos em duas cópias isoladas do MongoDB: com os índices atuais e com índices em employee_id e shipper_id. O PostgreSQL foi medido nas mesmas rodadas. Os resultados foram iguais nas três versões.

| Par | PostgreSQL (ms) | MongoDB, índices atuais (ms) | MongoDB com os novos índices (ms) | Redução no MongoDB |
|---|---|---|---|---|
| 04 | 1,506 | 3,941 | 2,867 | 27,3% |
| 13 | 0,416 | 2,341 | 1,793 | 23,4% |
| 15 | 1,364 | 5,855 | 5,330 | 9,0% |

| Par | Documentos examinados, índices atuais | Documentos examinados, com os novos índices |
|---|---|---|
| 04 | 7.470 | 830 |
| 13 | 4.980 | 830 |
| 15 | 7.470 | 1.746 |

Os índices reduziram o trabalho e o tempo, com intervalos Q1–Q3 sem sobreposição. Mesmo assim, o PostgreSQL continuou entre 1,9 e 4,3 vezes mais rápido. O índice explica parte da diferença; o resto vem da estratégia de um $lookup por documento e da conversão dos documentos pelo driver. Os índices foram testados só nas cópias; o banco original não foi alterado.

## 16.4 Estudos de otimização

Quatro consultas foram reescritas ou receberam índices em cópias isoladas dos dados. Em cada estudo, todas as versões rodaram nas mesmas rodadas, em ordem alternada, e devolveram o mesmo resultado. Quando os intervalos Q1–Q3 se sobrepõem, a diferença é tratada como inconclusiva.

| Estudo | Versão testada | PostgreSQL: mediana (Q1–Q3), ms | MongoDB: mediana (Q1–Q3), ms |
|---|---|---|---|
| C01 | original | 0,470 (0,452–0,492) | 1,007 (0,958–1,062) |
| C01 | reescrita | 0,364 (0,347–0,385) | 0,684 (0,676–0,731) |
| C01 | com_indice | 0,322 (0,310–0,347) | 0,507 (0,488–0,526) |
| C02 | sem_composto | 0,199 (0,183–0,206) | 0,644 (0,632–0,664) |
| C02 | com_composto | 0,173 (0,160–0,192) | 0,441 (0,429–0,477) |
| C03 | original | 3,353 (3,293–3,443) | 8,300 (8,062–8,710) |
| C03 | reescrita | 2,958 (2,871–3,059) | 8,137 (7,921–8,592) |
| C04 | original | 1,558 (1,470–1,630) | 6,440 (6,095–6,794) |
| C04 | reescrita | 1,301 (1,261–1,355) | 5,856 (5,700–6,007) |

**C01 — Filtro mensal.** A versão original calcula o mês de cada pedido com to_char (no MongoDB, $dateToString) e compara o texto; a reescrita filtra o intervalo de datas direto; a terceira versão acrescenta um índice em order_date. Redução da mediana — Reescrita do filtro: PostgreSQL 22,4%, MongoDB 32,1%; Índice por data: PostgreSQL 11,5%, MongoDB 25,9%.

**C02 — Cliente e período.** Pedidos de VINET em 1996, sem e com índice composto (customer_id, order_date). Redução da mediana — Índice composto: PostgreSQL 13,1% (inconclusivo), MongoDB 31,5%.

**C03 — Pares de produtos.** A versão original em SQL usa uma CTE MATERIALIZED que gera todos os pares antes de filtrar A < B; sem essa instrução, o próprio PostgreSQL já aplicaria o filtro na junção. No MongoDB, a original carrega o documento inteiro e só descarta os pares repetidos no fim. Redução da mediana — Reescrita: PostgreSQL 11,8%, MongoDB 2,0% (inconclusivo).

**C04 — Vendas da equipe.** A versão original junta a hierarquia com cada pedido e só depois soma; a reescrita soma os pedidos por funcionário antes de juntar. Redução da mediana — Reescrita: PostgreSQL 16,5%, MongoDB 9,1%.

Os resultados confirmam o que se esperava de cada mudança: filtrar pela coluna, e não por uma função dela, e indexar o acesso mais seletivo trouxeram os maiores ganhos; reduzir resultados intermediários ajudou no PostgreSQL e teve efeito pequeno ou inconclusivo no MongoDB.

## 16.5 Limites

Os dados cabem em memória e as consultas levam poucos milissegundos, então parte do tempo medido é comunicação e conversão de tipos pelo driver. Não foram medidos concorrência, escrita, grandes volumes nem distribuição em vários servidores. Durante as medições, outros containers sem relação com o projeto estavam ativos na máquina, o que pode acrescentar variação, mas afeta os dois bancos igualmente, porque as execuções foram intercaladas.
