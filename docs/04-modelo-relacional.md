# 04 — Modelo Relacional: o schema `nw`

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Data: 31/08/2026
>
> Scripts: `sql/10_ddl.sql` · `sql/20_load.sql` · `sql/30_indexes.sql` · `sql/40_views.sql`
> Evidências: `apresentacao/evidencias/03-validacao-carga-nw.txt` e `04-indices-e-views.txt`

---

## 1. Por que existe um segundo schema

O schema `public` guarda o Northwind original, **intocado**. O schema `nw` é o
modelo deste projeto.

A separação não é capricho: sem ela, "implementar um modelo relacional" viraria
"carregar um dump pronto", e não haveria nenhuma decisão de modelagem para
defender. Com ela, cada diferença entre os dois schemas é uma decisão registrada
— e o original continua ali do lado para comparação.

O `nw` implementa as 11 entidades de `docs/02` e corrige, uma a uma, as
fraquezas medidas em `docs/01` §4.

| Conceitual (`docs/02`) | Tabela em `nw` | Origem em `public` |
|---|---|---|
| FORNECEDOR | `suppliers` | `suppliers` |
| CATEGORIA | `categories` | `categories` |
| PRODUTO | `products` | `products` |
| ITEM DO PEDIDO | `order_items` | `order_details` |
| PEDIDO | `orders` | `orders` |
| CLIENTE | `customers` | `customers` |
| FUNCIONÁRIO | `employees` | `employees` |
| TRANSPORTADORA | `shippers` | `shippers` |
| TERRITÓRIO | `territories` | `territories` |
| REGIÃO | `regions` | `region` |
| ATUAÇÃO | `employee_territories` | `employee_territories` |

Duas tabelas mudaram de nome. `order_details` virou `order_items` porque
"detalhe" não diz o que a linha é, e a entidade conceitual chama-se ITEM DO
PEDIDO. `region` virou `regions` por consistência com o resto — e porque
`region` no singular colide com a coluna `region` que existe em quatro tabelas.

---

## 2. O que o banco passou a impedir

Esta é a mudança mais importante, e cabe numa tabela:

| | `public` (origem) | `nw` (projeto) |
|---|---:|---:|
| PRIMARY KEY | 14 | 11 |
| FOREIGN KEY | 13 | 11 |
| **UNIQUE** | **0** | **4** |
| **CHECK** | **0** | **17** |
| Colunas obrigatórias que antes aceitavam nulo | — | **21** |

*(Medido em `03-validacao-carga-nw.txt` §6 e §7. As contagens de PK e FK caem de
14/13 para 11/11 porque três tabelas ficaram fora do modelo — as duas vazias e a
`us_states`.)*

O banco de origem tinha integridade **referencial** perfeita e **nenhuma**
integridade de domínio: aceitaria quantidade negativa, desconto de 300% e pedido
enviado antes de ter sido feito. Agora não aceita.

O ponto que vale repetir na defesa: **a constraint não existe para descrever o
que os dados são, existe para impedir o que eles não podem virar.** Os 3311
registros passaram por todas as 17 regras novas sem uma única violação — a carga
rodou com `ON_ERROR_STOP=1` e saiu com código 0.

### As correções de tipo

| Coluna | Era | Virou | Por quê |
|---|---|---|---|
| Todos os valores em dinheiro | `real` | `numeric(10,2)` | ponto flutuante não representa 0,05 exatamente; o erro depende da ordem da soma |
| `order_items.discount` | `real` | `numeric(4,3)` | mesmo motivo, com a precisão que a regra de negócio pede |
| `products.discontinued` | `integer` 0/1 | `boolean` | o dado sempre foi booleano; o tipo agora diz isso |
| `orders.order_id` | `smallint` | `integer` | o teto de 32 767 já estava a 1/3 do caminho |
| `region_description` | — | `region_name` | o nome antigo descrevia o tipo, não o significado |

---

## 3. Normalização, com exemplo do próprio Northwind

As três formas normais, cada uma com o caso concreto desta base.

### 1FN — cada campo guarda um valor só

**Onde a base cumpre.** Os produtos vendidos não estão em `produto_1`,
`produto_2`, `produto_3` dentro do pedido: estão em `order_items`, uma linha por
produto. Se estivessem em colunas repetidas, seria preciso fixar um teto
arbitrário, e o pedido com um produto a mais quebraria o modelo.

**Onde a base NÃO cumpre — e eu deixei assim, de propósito.**
`products.quantity_per_unit` guarda coisas como `"10 boxes x 20 bags"`. São
quatro informações espremidas num texto: quantidade, embalagem externa,
quantidade interna e unidade. Não é atômico, logo viola a 1FN.

Mantive porque separar exigiria **interpretar 77 textos heterogêneos** e chutar
o significado de vários deles — e porque nenhuma das 16 perguntas de negócio usa
esse campo. É uma violação **declarada**, não uma que passou despercebida.

### 2FN — nada depende de só um pedaço da chave composta

A tabela que importa aqui é `order_items`, cuja chave é o par
`(order_id, product_id)`.

O caso interessante é `unit_price`. Se ela significasse "o preço do produto",
dependeria apenas de `product_id` — metade da chave — e seria violação de 2FN.
Mas ela significa **o preço praticado naquela venda**, que depende do pedido
*e* do produto. Depende da chave inteira. Está correto.

A prova de que os dois preços são coisas diferentes está nos dados: **662 dos
2155 itens (30,7%) têm preço de venda diferente do preço de catálogo atual.**

O contra-exemplo ajuda a fixar: se eu tivesse guardado `product_name` dentro de
`order_items`, aí sim seria violação — o nome do produto depende só de
`product_id`.

### 3FN — nenhum campo comum determina outro campo comum

Se `orders` guardasse `customer_company_name`, haveria uma cadeia
`order_id → customer_id → company_name`: dependência transitiva, violação de
3FN. Bastaria o cliente mudar de razão social para os pedidos antigos passarem a
mentir. Por isso `orders` guarda **só** `customer_id`.

**A pergunta difícil:** e as seis colunas `ship_*` do pedido, que em 94% dos
casos são cópia literal do endereço do cliente?

Não violam a 3FN — e o motivo é preciso. Dependência funcional não é "os valores
costumam coincidir", é "conhecer A **determina** B". Conhecer o cliente **não**
determina o endereço de entrega daquele pedido: **48 dos 830 pedidos (5,8%)
foram entregues em endereço diferente do cadastro.** O endereço de entrega é
atributo do pedido, não do cliente.

O que existe ali é outra coisa, e é honesto declarar: **falta uma entidade**. O
modelo ideal teria os endereços do cliente como entidade própria, e o pedido
referenciaria qual foi usado. Não implementei porque exigiria inventar
identificadores de endereço e decidir o que fazer com os 48 divergentes — e
porque a decisão não muda nenhuma das 16 perguntas. Fica registrada como dívida
consciente.

*(Todas as 11 tabelas estão também em BCNF: em cada uma, todo determinante é
chave candidata.)*

---

## 4. Os três lugares onde deliberadamente não normalizei

Normalizar até doer é tão errado quanto não normalizar. Os três casos, com o
critério que decidiu cada um:

1. **`order_items.unit_price` repete `products.unit_price`** — mantido. Não é
   redundância, é **snapshot histórico**: o preço da venda não pode mudar quando
   alguém reajusta a tabela de preços, senão o faturamento do ano passado se
   altera sozinho.
2. **As seis colunas `ship_*` de `orders`** — mantidas. Não violam 3FN (ver
   acima) e cobrem um caso real de negócio. A entidade de endereço que faltou
   está declarada como dívida.
3. **`products.quantity_per_unit` como texto livre** — mantido, violando 1FN,
   pelo custo de interpretação contra benefício zero para as perguntas do
   projeto.

O critério em uma frase: **normalizei tudo que tinha dependência funcional real;
deixei como está o que só parecia redundante.**

---

## 5. Índices: quatro entraram, cinco foram recusados

Nenhum índice entrou sem `EXPLAIN` provando que o planejador o escolhe.

| Índice | Serve às perguntas | Plano medido |
|---|---|---|
| `orders (customer_id)` | 06, 10, 11 | Bitmap Index Scan |
| `orders (employee_id)` | 04, 15 | Bitmap Index Scan |
| `orders (order_date)` | 02, 08, 09, 16 | **Index Only Scan** |
| `order_items (product_id)` | 01, 07, 12 | Bitmap Index Scan |

**O que explica quase todas as recusas:** a base é minúscula. A maior tabela,
`orders`, ocupa **15 páginas de 8 kB**. Ler 15 páginas inteiras é barato, então o
planejador só troca a varredura por índice quando o filtro é bem seletivo.

Os cinco recusados, por motivo:

- **`order_items (order_id)`** — redundante. A PK é `(order_id, product_id)` e
  começa por `order_id`, então ela mesma atende. *Um índice composto só serve
  para busca que começa pela primeira coluna* — é por isso que este é
  desnecessário e o de `product_id` é necessário.
- **`orders (customer_id, order_date)`** — composto, criado para o caso clássico
  "últimos pedidos do cliente X". O planejador **ignorou** e preferiu ler o
  índice de data ao contrário. O plano ficou idêntico com e sem ele.
- **`products (category_id)`, `products (supplier_id)`, `territories (region_id)`,
  `employee_territories (territory_id)`** — essas tabelas ocupam **uma** página.
  Ler a página custa um acesso; ler o índice e depois a tabela custa dois.

Em produção, com milhões de pedidos, vários desses passariam a valer a pena. A
decisão vale para **este** volume, e está registrada assim de propósito.

---

## 6. Quatro views, nenhuma decorativa

| View | Responde | Serve às perguntas |
|---|---|---|
| `vw_venda_item` | uma linha por produto vendido, com receita calculada | 01, 04, 07, 10, 11, 14, 16 |
| `vw_pedido_resumo` | uma linha por pedido: valor, itens e prazos | 02, 06, 13 |
| `vw_estoque_critico` | o que está abaixo do ponto de reposição | 05 |
| `vw_hierarquia_funcionarios` | a árvore da equipe, por **CTE recursiva** | 15 |

Elas existem porque o cálculo de receita —
`preço × quantidade × (1 − desconto)` — apareceria em 11 das 16 consultas, e
cálculo repetido é cálculo que uma hora sai diferente em algum lugar.

**Um detalhe que a banca pode cobrar.** A receita total pela view dá
**1.265.793,29**, e a soma sem arredondar dá **1.265.793,04**. A diferença de
R$ 0,25 é proposital: a view arredonda **cada item**, como faz uma nota fiscal,
onde toda linha tem um valor em centavos. Arredondar só no fim daria um total
que não bate com a soma das linhas impressas.

---

## 7. Reproduzir do zero

```bash
docker compose up -d
docker compose exec -T postgres psql -U pi -d northwind -f /sql/10_ddl.sql
docker compose exec -T postgres psql -U pi -d northwind -f /sql/20_load.sql
docker compose exec -T postgres psql -U pi -d northwind -f /sql/21_validacao_carga.sql
docker compose exec -T postgres psql -U pi -d northwind -f /sql/30_indexes.sql
docker compose exec -T postgres psql -U pi -d northwind -f /sql/40_views.sql
docker compose exec -T postgres psql -U pi -d northwind -f /sql/50_evidencias.sql
```

Os scripts são idempotentes: `10_ddl.sql` recria o schema do zero e `20_load.sql`
trunca antes de inserir. Rodar duas vezes dá o mesmo resultado.
