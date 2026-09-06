# 02 — Compreensão do Negócio

> **Entrega 01** · Fase 1 do CRISP-DM
> Autor: Giovanne Espíndola · Data: 05/09/2026

---

## 1. O contexto

A **Northwind Traders** é uma **importadora e distribuidora de alimentos
especializados**. Ela não fabrica nada: compra de fornecedores no mundo inteiro
e revende para clientes corporativos — restaurantes, mercados, delicatessens.

O ciclo que a base registra é o clássico **order-to-cash** (do pedido ao
recebimento), e ele acontece assim:

Um **fornecedor** (29 deles) vende à Northwind um conjunto de **produtos** (77).
Cada produto pertence a exatamente uma **categoria** (8 — bebidas, laticínios,
frutos do mar…) e a exatamente um fornecedor. O produto tem preço de tabela,
saldo em estoque, quantidade já encomendada ao fornecedor, um ponto de reposição
e uma marca de descontinuado.

Do outro lado está o **cliente** (91), uma empresa identificada por um código de
cinco letras — `ALFKI`, `BERGS`, `FISSA`. Quando ele compra, nasce um **pedido**
(830). O pedido não guarda o que foi comprado: guarda o cabeçalho da venda —
quem comprou, qual **funcionário** (9) fechou a venda, quando foi feito, para
quando foi prometido, quando de fato saiu, por qual **transportadora** (6) foi,
quanto custou o frete e para onde foi entregue.

O que foi comprado está nos **itens do pedido** (2 155 linhas): uma linha por
produto dentro do pedido. Cada linha guarda quantidade, preço unitário **daquela
venda** e desconto aplicado. É aqui que mora o dinheiro — a receita da empresa é
`quantidade × preço unitário × (1 − desconto)`, somada sobre estas 2 155 linhas.

Existe ainda uma estrutura comercial de território: o país é dividido em
**regiões** (4) que se subdividem em **territórios** (53), e cada funcionário
responde por um conjunto deles (49 vínculos). E os funcionários se organizam em
hierarquia: cada um aponta para o seu superior dentro da própria tabela.

Em uma frase:

> **A Northwind compra de fornecedores, cataloga em produtos, vende através de
> funcionários para clientes empresariais, e entrega via transportadoras.**

## 2. O que os dados representam

As 14 tabelas da base se dividem em quatro papéis de negócio distintos. Essa
separação é o que orienta toda a modelagem posterior:

| Papel | Tabelas | O que representam |
|---|---|---|
| **Transação** — o que aconteceu | `orders`, `order_details` | o evento de venda: o cabeçalho e os itens. São os dados que **crescem** com a operação e onde está a receita. |
| **Cadastro** — quem e o quê | `customers`, `products`, `employees`, `suppliers`, `shippers` | as entidades estáveis que participam da venda. Mudam devagar. |
| **Classificação** — como se agrupa | `categories`, `region`, `territories` | as dimensões pelas quais o negócio quer enxergar os números. |
| **Vínculo** — quem responde por quê | `employee_territories` | a malha de cobertura comercial. |

Duas tabelas ficam de fora dessa leitura porque **não representam nada na
prática**: `customer_demographics` e `customer_customer_demo` estão vazias, e
`us_states` não tem nenhuma chave estrangeira apontando para ela — é uma tabela
ilha, desconectada do modelo.

A distinção que mais importa para este trabalho é a primeira: **transação versus
cadastro**. É ela que determina o que vira documento no MongoDB e o que
permanece referência — um pedido fechado nunca muda, um cadastro de cliente
muda o tempo todo.

## 3. As informações que se pretende obter

Lista **fechada** de 16 perguntas, que orienta as entregas seguintes. Cada
pergunta será respondida **duas vezes** — uma em SQL e uma em pipeline de
agregação do MongoDB — e é essa duplicação que produz a análise comparativa e a
base do benchmark.

| # | Pergunta de negócio | Recurso técnico exercitado |
|---|---|---|
| 01 | Qual o faturamento por categoria de produto? | junção + agregação |
| 02 | Qual o ticket médio mês a mês? | agregação temporal |
| 03 | Que produtos nunca foram vendidos? | anti-junção |
| 04 | Quanto cada vendedor faturou? | junção + agrupamento |
| 05 | Que produtos estão com estoque abaixo do ponto de reposição? | filtro + comparação entre colunas |
| 06 | Que clientes não compram há mais de 6 meses? | data + anti-junção |
| 07 | Quais os 5 produtos mais vendidos **dentro de cada** categoria? | *window function* (`RANK`) |
| 08 | Como evolui o faturamento acumulado mês a mês? | *running total* |
| 09 | Qual a variação percentual de receita de um mês para o outro? | `LAG` |
| 10 | Quais clientes formam a curva ABC (20% que fazem 80%)? | `NTILE` / percentil |
| 11 | Como segmentar clientes por Recência, Frequência e Valor (RFM)? | CTEs encadeadas |
| 12 | Que produtos são comprados juntos no mesmo pedido? | auto-junção / `$unwind` duplo |
| 13 | Qual o prazo médio de entrega por transportadora? | diferença de datas |
| 14 | Qual o impacto do desconto sobre a receita? | cálculo derivado |
| 15 | Quanto vende a equipe de cada gerente, somando os subordinados? | **CTE recursiva** vs `$graphLookup` |
| 16 | Existe sazonalidade por trimestre? | `GROUPING SETS` / `$facet` |

As perguntas 07 a 16 são as que demonstram domínio além do agrupamento simples —
e são justamente as que expõem as diferenças reais entre os dois modelos de banco.

### 3.1 Duas perguntas que os dados obrigaram a reescrever

Este é o vaivém entre as fases 1 e 2 do CRISP-DM, na prática. As duas perguntas
abaixo foram formuladas antes de olhar a base, e a análise exploratória mostrou
que a base não as respondia:

| Pergunta original | O que os dados mostraram | Pergunta final |
|---|---|---|
| "Que produtos estão com estoque baixo?" | "baixo" não é critério — mas a base tem uma coluna de **ponto de reposição** por produto | "Que produtos estão com estoque **abaixo do ponto de reposição**?" (05) |
| "Qual o impacto do desconto sobre a **margem**?" | a base tem preço de venda, **não tem custo de aquisição** — margem é incalculável | "Qual o impacto do desconto sobre a **receita**?" (14) |

Reescrever a pergunta é o comportamento correto: o erro seria manter a pergunta
original e responder com um número inventado.

## 4. O que a base NÃO responde

Melhor declarar aqui do que descobrir na frente da banca:

- **não há custo de produto** — logo, não se calcula margem nem lucro, só receita;
- **não há cancelamento nem devolução** — todo pedido registrado é um pedido válido;
- **não há pagamento nem inadimplência** — o ciclo termina na entrega;
- **não há segmentação de cliente** — a estrutura existe, mas está vazia.
