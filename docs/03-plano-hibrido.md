# 03 — Plano Híbrido: PostgreSQL e MongoDB no mesmo projeto

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Data: 31/08/2026
>
> Diagrama: `docs/diagramas/arquitetura-hibrida.png`

---

## 1. A pergunta que este documento responde

O projeto inteiro gira em torno de **"qual a ferramenta certa para o trabalho?"**.
Este plano define como os dois bancos vão conviver e, principalmente, **como a
comparação entre eles vai ser feita de um jeito que o resultado signifique
alguma coisa**.

A resposta não é "o relacional é melhor" nem "o documental é mais moderno". É
uma pergunta anterior: **qual é a forma dominante de acesso ao dado?** Tudo
depende disso, e é isso que o experimento vai medir.

---

## 2. O que cada banco faz bem — por critério, não por adjetivo

| | PostgreSQL | MongoDB |
|---|---|---|
| **Unidade natural** | a linha, ligada por chave | o documento, lido inteiro |
| **Integridade** | declarativa: o banco recusa o que viola | da aplicação, ou por *validator* opcional |
| **Pergunta imprevista** | `JOIN` responde o que ninguém antecipou | precisa de `$lookup`, ou de remodelar |
| **Leitura do agregado** | reconstruir exige junção | uma leitura, sem junção |
| **Escala** | vertical, e réplicas de leitura | horizontal, por *sharding* |
| **Transação multi-entidade** | nativa desde sempre | existe, mas é caminho menos trilhado |

A linha que mais importa é a terceira. **Modelo relacional é o que permite fazer
uma pergunta que não foi prevista na hora de modelar.** Modelo documental é o
que permite servir rápido a pergunta que *foi* prevista.

---

## 3. A arquitetura escolhida

```
  aplicação / carga                consultas analíticas
         │                                  │
         ▼                                  ▼
  ┌─────────────────┐   ETL em lote   ┌──────────────────┐
  │  PostgreSQL nw  │ ──────────────▶ │     MongoDB      │
  │ fonte da verdade│  idempotente,   │ cópia documental │
  │ constraints, FK │  unidirecional  │  agregados       │
  └─────────────────┘                 └──────────────────┘
```

**O PostgreSQL é a fonte da verdade.** É onde a venda acontece, onde as 17
constraints impedem o dado inválido de entrar, e onde a transação garante que
pedido e itens nascem juntos ou não nascem.

**O MongoDB é uma cópia orientada a documento**, alimentada por `etl/migrate.py`.
Ele não recebe escrita de aplicação neste projeto.

### Por que o fluxo é de mão única

Sincronizar nos dois sentidos exigiria decidir quem ganha quando os dois lados
mudam o mesmo dado — e qualquer resposta a isso é arbitrária. **Um dado com dois
donos é um dado sem dono.** Mão única elimina a pergunta.

### Por que ETL em lote, e não replicação em tempo real

Captura de mudança em tempo real (CDC) existe e funciona — Debezium lendo o WAL
do PostgreSQL, Kafka no meio. Seria a escolha certa para um sistema com
requisito de latência.

Este projeto não tem esse requisito, e a complexidade seria maior que o problema:
mais dois serviços para o avaliador subir, e nenhuma das 16 perguntas de negócio
melhora com dados de um segundo atrás. **Lote idempotente, que qualquer um roda
com um comando, vale mais aqui do que arquitetura de streaming.**

---

## 4. O desenho do documento — o que muda de um lado para o outro

A decisão fecha na Entrega 02, mas o caminho já está definido, e ele é o que
torna a comparação interessante:

| Coleção | Estratégia | Por quê |
|---|---|---|
| `orders` | **agregado central**: itens embutidos como array, com *snapshot* do cliente e do vendedor | um pedido é lido inteiro ou não é lido; item não existe fora do pedido; nada muda depois que o pedido fecha |
| `products` | categoria e fornecedor como *extended reference* | quem lê um produto quase sempre quer o nome da categoria junto — mas não o resto dela |
| `customers` | endereço embutido | endereço não é consultado sozinho |
| `employees` | hierarquia por referência (`reports_to`) | árvore de profundidade variável; embutir criaria aninhamento sem fim |

**A tradução que importa:** as 830 linhas de `orders` mais as 2155 de
`order_items` viram **830 documentos**. A junção que o PostgreSQL faz em tempo
de consulta, o MongoDB faz em tempo de escrita — uma vez só, no ETL.

É exatamente aí que está o *trade-off* do projeto: o documental **paga
antecipado** o custo da junção e cobra caro quando você quer cruzar de um jeito
que ele não previu.

---

## 5. Como a comparação vai ser feita

**Um conjunto único de perguntas, respondido duas vezes.** As 16 perguntas de
negócio de `docs/01` §6 viram 16 consultas SQL (`sql/queries/QNN.sql`) e 16
pipelines de agregação (`mongo/pipelines/PNN.js`). `Q07` e `P07` respondem
exatamente à mesma pergunta.

Isso produz três entregáveis de uma vez: as consultas da Entrega 03, a análise
comparativa de sintaxe, e a base do benchmark da Entrega 04.

**A regra que sustenta o resultado:** se `QNN` e `PNN` derem números diferentes,
**o trabalho para até a causa ser encontrada.** Divergência não é bug para
esconder, é material de análise — normalmente ela revela uma diferença real de
semântica entre os dois modelos, e essa diferença é o achado.

**Protocolo do benchmark:** descartar a primeira execução (que paga o
aquecimento de cache), rodar N ≥ 10, reportar a **mediana** — não a média, que
um único pico distorce. Mesmo container, mesma máquina, sem carga concorrente.

---

## 6. O que este experimento NÃO prova — declarado antes de medir

Esta seção existe para que nenhuma conclusão seja mais forte do que os dados
permitem.

1. **Volume.** São 830 pedidos e 2155 itens. Tudo roda em milissegundos nos dois
   bancos. O benchmark **não prova escalabilidade**; mede como cada tecnologia se
   comporta nesta escala e como cada consulta se escreve.
2. **Nó único.** O MongoDB roda sem *sharding* e sem *replica set*. A principal
   vantagem estrutural do documental — distribuir por muitas máquinas — **não é
   exercitada**. Comparar sem isso favorece o relacional, e é honesto dizer.
3. **Sem concorrência.** Mede-se latência de consulta isolada, não vazão sob
   carga. São coisas diferentes.
4. **Sem custo de produto.** A base não tem custo de aquisição, então nenhuma
   pergunta calcula margem — só receita.

---

## 7. O critério que vai decidir a resposta final

No fim, "qual a ferramenta certa" será respondido por esta matriz, preenchida
com medição na Entrega 04:

| Critério | Vence quem |
|---|---|
| Servir um pedido inteiro para uma tela ou API | menos junção |
| Responder pergunta analítica não prevista | mais expressividade de consulta |
| Impedir dado inválido de entrar | mais garantia declarativa |
| Clareza de quem escreve a consulta | menos linhas para o mesmo resultado |
| Custo de mudar o modelo depois | menos migração |

**A hipótese que o projeto vai testar** — e que pode ser refutada pelos dados:
para o Northwind, o pedido é um agregado de livro-texto e o MongoDB deve vencer
na leitura operacional; mas as 16 perguntas cruzam categoria, tempo, vendedor e
cliente de formas variadas, e aí o `JOIN` deve vencer. Se for isso, a resposta
correta não é escolher um — é **usar cada um para o que ele é**, que é a razão de
o plano se chamar híbrido.

---

## 8. Próximo passo

Entrega 02: implementar o modelo de documentos aqui esboçado, escrever os
*validators*, construir `etl/migrate.py` idempotente e validar que os totais
batem nos dois bancos.
