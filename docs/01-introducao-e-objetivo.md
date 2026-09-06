# 01 — Introdução e Objetivo

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Trabalho **individual** · Data: 05/09/2026

---

## 1. O objetivo do trabalho

Este projeto responde a uma pergunta de decisão técnica:

> **Qual a ferramenta certa para o trabalho?**

Não "qual banco de dados é melhor" — assim posta, a pergunta não tem resposta.
A formulação útil é: **qual é a forma dominante de acesso ao dado, e qual
tecnologia serve melhor a ela?**

Para responder, o mesmo domínio de negócio é modelado e implementado **duas
vezes**: uma vez em um banco **relacional** (PostgreSQL 16) e uma vez em um
banco **orientado a documentos** (MongoDB 7). As mesmas 16 perguntas de negócio
são respondidas nas duas tecnologias, e a conclusão sai da diferença medida —
não de opinião.

O objetivo, portanto, é duplo:

1. **Objetivo de negócio** — extrair de uma base de vendas as informações que
   sustentam decisão comercial: onde está a receita, quem vende, o que encalha,
   quem deixou de comprar.
2. **Objetivo técnico** — usar essas mesmas perguntas como instrumento de
   comparação entre dois paradigmas de armazenamento, produzindo uma
   recomendação justificada por evidência executada.

## 2. A metodologia: CRISP-DM

O trabalho é conduzido segundo o **CRISP-DM** (*CRoss-Industry Standard Process
for Data Mining*), o processo de referência para projetos de dados, publicado em
2000 por um consórcio de indústria e ainda hoje a metodologia mais usada na
área. Ele organiza um projeto de dados em **seis fases**:

| # | Fase | O que se faz nela |
|---|---|---|
| 1 | **Entendimento do negócio** | descobrir o que o negócio precisa saber, e traduzir isso em perguntas respondíveis |
| 2 | **Entendimento dos dados** | conhecer a base: o que ela contém, como se relaciona, em que estado está |
| 3 | **Preparação dos dados** | corrigir, tipar, restringir e transformar até os dados servirem ao uso |
| 4 | **Modelagem** | construir o modelo que responde às perguntas |
| 5 | **Avaliação** | verificar se o modelo responde de fato, e comparar alternativas |
| 6 | **Implantação** | entregar de forma que outra pessoa consiga usar e reproduzir |

O CRISP-DM **não é uma escada** — é um ciclo. Suas fases se retroalimentam: foi
o entendimento dos dados (fase 2) que forçou a reescrever duas das perguntas de
negócio (fase 1), porque a base não tinha como respondê-las. Esse vaivém está
documentado, e é ele que justifica a escolha da metodologia.

### 2.1 Como as fases se distribuem nas entregas

| Fase do CRISP-DM | Neste projeto | Entrega |
|---|---|---|
| 1. Entendimento do negócio | processo *order-to-cash* da Northwind; as 16 perguntas | **01** |
| 2. Entendimento dos dados | perfilamento, avaliação de qualidade e ER conceitual | **01** |
| 3. Preparação dos dados | schema próprio com tipos corrigidos e regras explícitas; ETL para o MongoDB | 02 |
| 4. Modelagem | modelo relacional normalizado **e** modelo de documentos | 02 |
| 5. Avaliação | as 16 perguntas respondidas nas duas tecnologias; benchmark comparativo | 03 e 04 |
| 6. Implantação | repositório reproduzível, relatório final e apresentação | 04 |

**Esta entrega cobre as fases 1 e 2.**

### 2.2 Uma adaptação que precisa ser declarada

No CRISP-DM original, "Modelagem" significa **modelo estatístico ou de
aprendizado de máquina** — o processo nasceu em mineração de dados. Aqui,
"modelagem" significa **modelo de dados**: o esquema relacional e o esquema de
documentos.

A adaptação é legítima e comum em projetos de engenharia de dados, mas é melhor
declará-la do que ser questionado sobre ela: o que muda é o *artefato* produzido
na fase 4, não a lógica do processo. As fases continuam fazendo o mesmo papel —
entender antes de preparar, preparar antes de modelar, avaliar antes de entregar.

## 3. O domínio escolhido

**Northwind Traders**, uma distribuidora de alimentos importados. É um dataset
clássico de ensino, escolhido por três razões concretas:

1. **Tem processo de negócio completo**: catálogo, fornecedores, clientes,
   pedidos, itens, vendedores, territórios e entrega. Dá para fazer pergunta de
   negócio de verdade, não exercício sintético.
2. **Tem os dois casos que interessam à comparação**: um agregado natural (o
   pedido com seus itens, lido inteiro) *e* perguntas analíticas que cruzam
   entidades de formas variadas. Um dataset com apenas um dos dois enviesaria a
   comparação por construção.
3. **É pequeno o suficiente para ser reproduzível** por qualquer avaliador com
   Docker, e grande o suficiente para ter irregularidades reais — que são o
   material da análise.

**Volume:** 14 tabelas, 3 362 linhas, pedidos de 04/07/1996 a 06/05/1998.

## 4. As tecnologias, e por que elas

### Por que PostgreSQL, e não MySQL

O enunciado deixa a escolha aberta. A escolha foi pelo PostgreSQL por cinco
recursos que **este trabalho usa de fato**:

| Recurso | Onde é usado aqui |
|---|---|
| **DDL transacional** — `CREATE TABLE` dentro de `BEGIN … ROLLBACK` | testar constraint e índice sem sujar o banco; o MySQL faz *commit* implícito em DDL, e o teste não teria volta |
| **Tipo `ARRAY`** | a view de hierarquia guarda o caminho até o topo num array |
| **Cláusula `FILTER (WHERE …)`** em agregação | todos os relatórios de validação; no MySQL vira `SUM(CASE WHEN … END)`, bem menos legível |
| **`EXPLAIN (… BUFFERS)`** | mostra quantas páginas cada plano toca; com ele metade das recusas de índice foi decidida em vez de opinada |
| **`COMMENT ON` em índice e schema** | a explicação de cada índice fica dentro do catálogo do banco; o MySQL só comenta tabela e coluna |

**Sendo justo com o MySQL** — e isso importa numa defesa: as críticas que
normalmente se fazem a ele **não valem mais**. Desde a versão 8.0 ele tem CTE
recursiva e *window functions*, e desde a 8.0.18 tem `EXPLAIN ANALYZE`. A
diferença real está nos itens da tabela, e a mais decisiva é a primeira: metade
das verificações feitas aqui só é possível porque dá para testar uma mudança de
schema e desfazê-la.

### E o MongoDB, foi escolha?

Não da mesma forma: o enunciado **define** o MongoDB como o lado documental. Mas
cabe justificar por que o modelo de documentos é o contraponto certo para *este*
domínio, porque é disso que a comparação depende:

- **Chave-valor** (Redis) guarda e devolve, não agrega — não responderia nenhuma
  das 16 perguntas.
- **Família de colunas** (Cassandra) é forte em escrita massiva e série temporal,
  não em ler um pedido inteiro nem em cruzar entidades.
- **Grafo** (Neo4j) resolveria bem a hierarquia de funcionários e a malha de
  territórios, mas essas são a periferia do domínio — o núcleo é transacional.
- **Documento** é o único que espelha o agregado mais característico do
  Northwind: **o pedido com seus itens**, lido inteiro, imutável depois de fechado.

## 5. Escopo

**Entra:**

- perfilamento e análise exploratória da base, com evidência executada
- modelo conceitual (ER), modelo relacional próprio com normalização
  justificada, constraints, índices e views
- modelo de documentos para MongoDB e migração idempotente
- 16 consultas SQL e 16 pipelines de agregação equivalentes
- benchmark comparativo e análise de sintaxe

**Não entra, e é declarado:**

- **margem de lucro** — a base não tem custo de aquisição de produto, só preço
  de venda. Toda análise financeira é de **receita**, nunca de margem.
- **cancelamento, devolução, pagamento e inadimplência** — não existem na base.
- **segmentação de clientes** — as tabelas existem e estão vazias (0 linhas).
- **escalabilidade** — 830 pedidos rodam em milissegundos nos dois bancos. O
  benchmark mede comportamento nesta escala, não capacidade de crescer.

## 6. Duas regras que o trabalho seguiu

**Nenhum número sem execução.** Todo valor que aparece em qualquer documento foi
produzido por um comando registrado ao lado dele, e a saída bruta está
versionada. Não há número estimado, arredondado de memória ou copiado de outro
trabalho.

**Reprodutibilidade é entregável.** Um avaliador com Docker e este repositório
levanta os dois bancos, carrega o Northwind, constrói o schema do projeto e
regera todas as evidências sem nenhum passo manual não documentado. O `README.md`
tem os comandos na ordem.
