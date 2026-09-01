# 00 — Definição do Trabalho e Área de Foco

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Trabalho **individual** · Data: 31/08/2026

---

## 1. Área de foco

**Modelagem e análise de dados de vendas**, com foco na escolha de tecnologia de
armazenamento — comparando uma solução **relacional** (PostgreSQL 16) com uma
**orientada a documentos** (MongoDB 7) sobre o mesmo domínio de negócio.

### Por que PostgreSQL, e não MySQL

O enunciado deixa a escolha aberta entre os dois. A escolha foi pelo PostgreSQL,
e não por gosto — por cinco recursos que **este trabalho usa de fato**:

| Recurso | Onde é usado aqui |
|---|---|
| **DDL transacional** — `CREATE TABLE` dentro de `BEGIN … ROLLBACK` | testar constraint e índice sem sujar o banco; o MySQL faz *commit* implícito em DDL, e o teste não teria volta |
| **Tipo `ARRAY`** | `vw_hierarquia_funcionarios` guarda o caminho até o topo da hierarquia num array |
| **Cláusula `FILTER (WHERE …)`** em agregação | todos os relatórios de validação; no MySQL vira `SUM(CASE WHEN … END)`, bem menos legível |
| **`EXPLAIN (… BUFFERS)`** | mostra quantas páginas cada plano toca, e foi com ele que metade das recusas de índice foi decidida em vez de opinada |
| **`COMMENT ON` em índice e schema** | os 4 índices e o próprio schema `nw` carregam a explicação dentro do catálogo; o MySQL só comenta tabela e coluna |

Na Entrega 03 entra ainda `GROUPING SETS`, para a pergunta 16 de sazonalidade —
o MySQL só tem `WITH ROLLUP`.

**Sendo justo com o MySQL**, e isso importa numa defesa: as coisas que
normalmente se citam contra ele **não valem mais**. Desde a versão 8.0 ele tem
CTE recursiva e *window functions*, que dão conta das perguntas 07 a 11 e 15, e
desde a 8.0.18 tem `EXPLAIN ANALYZE` — o que o PostgreSQL acrescenta ali é o
`BUFFERS`, não a medição em si. A diferença real está nos itens acima, e a mais
decisiva para *este* projeto é a primeira: metade das verificações feitas aqui só
é possível porque dá para testar uma mudança de schema e desfazê-la.

### E o MongoDB, foi escolha?

Não da mesma forma. O enunciado deixa o relacional em aberto ("PostgreSQL ou
MySQL") e **define** o MongoDB como o lado documental. Mas cabe justificar por
que o modelo de documentos é o contraponto certo para *este* domínio — porque é
disso que a comparação depende:

- **Chave-valor** (Redis) guarda e devolve, não agrega. Não responderia nenhuma
  das 16 perguntas.
- **Família de colunas** (Cassandra) é forte em escrita massiva e série temporal,
  não em ler um pedido inteiro nem em cruzar entidades.
- **Grafo** (Neo4j) resolveria bem a hierarquia de funcionários e a malha de
  territórios, mas essas são a periferia do domínio — o núcleo é transacional.
- **Documento** é o único que espelha o agregado que o Northwind tem de mais
  característico: **o pedido com seus itens**, lido inteiro, imutável depois de
  fechado.

E entre os documentais, o MongoDB tem *aggregation pipeline* com expressividade
comparável à do SQL — sem isso, comparar as 16 perguntas nas duas tecnologias não
seria uma comparação, seria uma demonstração de que uma delas não dá conta.

## 2. O domínio

**Northwind Traders**, uma distribuidora de alimentos importados. É um dataset
clássico de ensino, e foi escolhido por três razões concretas, não por tradição:

1. **Tem processo de negócio completo**: catálogo, fornecedores, clientes,
   pedidos, itens, vendedores, territórios e entrega. Dá para fazer pergunta de
   negócio de verdade, não exercício sintético.
2. **Tem os dois casos que interessam à comparação**: um agregado natural (o
   pedido com seus itens, que se lê inteiro) *e* perguntas analíticas que cruzam
   entidades de formas variadas. Um dataset que só tivesse um dos dois tornaria a
   comparação enviesada por construção.
3. **É pequeno o suficiente para ser reproduzível** por qualquer avaliador com
   Docker, e grande o suficiente para ter irregularidades reais — que são o
   material da análise.

**Volume:** 14 tabelas, 3362 linhas, pedidos de 04/07/1996 a 06/05/1998.

## 3. A pergunta central

> **Qual a ferramenta certa para o trabalho?**

Não "qual banco é melhor" — a pergunta assim posta não tem resposta. A
formulação útil é: **qual é a forma dominante de acesso ao dado, e qual
tecnologia serve melhor a ela?**

O trabalho responde isso com medição, não com opinião: as mesmas 16 perguntas de
negócio são respondidas nas duas tecnologias, e a comparação sai da diferença.

## 4. Escopo

**Entra:**

- perfilamento e análise exploratória da base, com evidência executada
- modelo conceitual (ER), modelo relacional próprio com normalização justificada,
  constraints, índices e views
- modelo de documentos para MongoDB e migração idempotente
- 16 consultas SQL e 16 pipelines de agregação equivalentes
- benchmark comparativo e análise de sintaxe

**Não entra, e é declarado:**

- **margem de lucro** — a base não tem custo de aquisição de produto, só preço de
  venda. Toda análise financeira é de **receita**, nunca de margem.
- **cancelamento, devolução, pagamento e inadimplência** — não existem na base.
- **segmentação de clientes** — as tabelas existem e estão vazias (0 linhas).
- **escalabilidade** — 830 pedidos rodam em milissegundos nos dois bancos. O
  benchmark mede comportamento nesta escala, não capacidade de crescer.

## 5. Como o trabalho está organizado

| Entrega | Conteúdo | Data |
|---|---|---|
| 01 | ER conceitual, Plano Híbrido, modelo relacional implementado | 06/09/2026 |
| 02 | Modelagem NoSQL e migração | 13/09/2026 |
| 03 | 16 consultas SQL e 16 pipelines equivalentes | 27/09/2026 |
| 04 | Benchmark, relatório final e apresentação | 08/10/2026 |

Os documentos seguem a mesma numeração. Esta entrega traz `docs/00` a `docs/04`.

## 6. Duas regras que o trabalho seguiu

**Nenhum número sem execução.** Todo valor que aparece em qualquer documento foi
produzido por um comando que está registrado ao lado dele, e a saída bruta está
em `apresentacao/evidencias/`. Não há número estimado, arredondado de memória ou
copiado de outro trabalho.

**Reprodutibilidade é entregável.** Um avaliador com Docker e este repositório
levanta os dois bancos, carrega o Northwind, constrói o schema do projeto e
regera todas as evidências sem nenhum passo manual não documentado. O `README.md`
tem os comandos na ordem.
