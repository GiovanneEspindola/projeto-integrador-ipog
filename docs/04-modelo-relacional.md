# 04 — Modelo Relacional: o schema `nw`

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Data: 31/08/2026
>
> Scripts: `sql/10_ddl.sql` · `sql/20_load.sql` · `sql/30_indexes.sql` · `sql/40_views.sql`
> Diagrama: `docs/diagramas/er-logico.png` · fonte: `docs/diagramas/nw-schema.dbml`
> Evidências: `apresentacao/evidencias/03-validacao-carga-nw.txt` e `04-indices-e-views.txt`

---

## 1. Por que existe um segundo schema

O schema `public` guarda o Northwind original, **intocado**. O schema `nw` é o
modelo deste projeto.

A separação não é capricho: sem ela, "implementar um modelo relacional" viraria
"carregar um dump pronto", e não haveria nenhuma decisão de modelagem para
defender. Com ela, cada diferença entre os dois schemas é uma decisão registrada
— e o original continua ali do lado para comparação.

O `nw` implementa as 11 entidades de `docs/02` e enfrenta, uma a uma, as
fraquezas medidas em `docs/01` §4 — corrigindo a maioria e **declarando** as que
decidiu não corrigir.

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

Três colunas também mudaram de nome, sempre pelo mesmo motivo — o nome antigo
descrevia o mecanismo, não o significado:

| Em `public` | Em `nw` |
|---|---|
| `orders.ship_via` | `orders.shipper_id` |
| `region.region_description` | `regions.region_name` |
| `territories.territory_description` | `territories.territory_name` |

### O ER lógico

`docs/diagramas/er-logico.png` mostra o mesmo modelo com o que o conceitual
deliberadamente omitia: **tipo de dado, tamanho, obrigatoriedade e chave
estrangeira**. Colocados lado a lado, os dois diagramas explicam sozinhos por que
existem dois — o conceitual se discute com quem entende do negócio, o lógico com
quem vai construir.

Ele não foi desenhado à mão: `docs/diagramas/nw-schema.dbml` é **gerado do banco**
com `db2dbml`. Mas "gerado" não é garantia — basta o schema mudar depois para o
diagrama entregue passar a mentir. Por isso a correspondência é **verificada**, e
não presumida: `etl/valida_dbml.py` confere as 11 tabelas, as **81 colunas** com
nome, ordem, tipo **e obrigatoriedade**, e as **11 chaves estrangeiras** — cada
uma com origem e destino — contra o `information_schema`, saindo com código 1 em
qualquer divergência.

O validador foi testado por mutação em cinco frentes: alterando um tipo,
removendo uma coluna, removendo uma chave estrangeira, deixando uma FK com o nome
certo apontando para a coluna errada, e marcando como obrigatória uma coluna que
não é. Acusou as cinco. As duas últimas entraram depois de uma revisão flagrar
que o validador não as via.

```bash
npx -p @dbml/cli db2dbml postgres \
  'postgresql://pi:pi@localhost:5432/northwind?schemas=nw' -o docs/diagramas/nw-schema.dbml
uv run python etl/valida_dbml.py     # evidência: 05-validacao-er-logico.txt
```

---

## 2. O que o banco passou a impedir

Esta é a mudança mais importante, e cabe numa tabela:

| | `public` (origem) | `nw` (projeto) |
|---|---:|---:|
| PRIMARY KEY | 14 | 11 |
| FOREIGN KEY | 13 | 11 |
| **UNIQUE** | **0** | **4** |
| **CHECK** | **0** | **17** |
| Colunas obrigatórias que antes aceitavam nulo | — | **19** |

As 19 obrigatoriedades saem de três grupos, e nenhuma é gosto pessoal:
**as cinco colunas de junção** (`orders.customer_id`, `employee_id`,
`shipper_id`, `products.supplier_id`, `category_id`) — pedido sem cliente ou
produto sem categoria não existe no negócio; **as datas e os valores do pedido**
(`order_date`, `required_date`, `freight` e o endereço de entrega) — pedido sem
promessa de entrega não é pedido fechado numa distribuidora; e **os campos de
identificação e preço** de produtos e funcionários.

Duas ficaram de fora **de propósito, depois de revisão**: `categories.description`
e `products.quantity_per_unit` estavam obrigatórias só porque os dados de hoje as
preenchem — que é exatamente o erro que este documento critica duas seções
adiante. Categoria nova sem descrição e produto vendido a granel, que não tem
embalagem para descrever, são cadastros legítimos. No caso de
`quantity_per_unit` havia ainda uma contradição interna: a §3 declara a coluna
uma violação de 1FN mantida "porque nenhuma das 16 perguntas usa esse campo", e o
schema a exigia.

*(Medido em `03-validacao-carga-nw.txt` §6 e §7. As PKs caem de 14 para 11 porque
três tabelas ficaram fora — as duas vazias e a `us_states`. Já as FKs caem de 13
para 11 por causa de **uma só**: `customer_customer_demo` tinha duas; `us_states`
e `customer_demographics` não tinham nenhuma.)*

O banco de origem tinha integridade **referencial** perfeita e **nenhuma**
integridade de domínio: aceitaria quantidade negativa, desconto de 300% e pedido
enviado antes de ter sido feito. Agora não aceita.

O ponto que vale repetir na defesa: **a constraint não existe para descrever o
que os dados são, existe para impedir o que eles não podem virar.** Os 3311
registros passaram por todas as 17 regras novas sem uma única violação — a carga
rodou com `ON_ERROR_STOP=1` e saiu com código 0.

### E o schema opera, não só carrega

As sete chaves sintéticas são `GENERATED BY DEFAULT AS IDENTITY`. Sem isso o
modelo aceitaria a carga e depois não conseguiria registrar **uma venda nova**,
porque ninguém saberia qual id usar — teria que calcular `max(id)+1` na mão, que
além de trabalhoso não é seguro com dois usuários ao mesmo tempo.

`BY DEFAULT` e não `ALWAYS`: `BY DEFAULT` deixa a carga inserir os ids que vieram
da origem **e** permite que uma inserção normal, sem id, receba o próximo número.
Com `ALWAYS` toda instrução da carga precisaria de `OVERRIDING SYSTEM VALUE`.

Como a carga traz os ids prontos, as sequences ficariam paradas em 1 e o próximo
`INSERT` colidiria. Por isso `20_load.sql` termina com `setval` reposicionando
cada uma no maior id já usado — depois de uma carga limpa, a de `orders` fica em
**11077**, que é o maior `order_id` da base. Testado numa transação revertida: um
pedido inserido sem `order_id` recebeu **11078**, o número seguinte.

### Três colunas ficaram para trás, de propósito

`categories.picture` e `employees.photo` são `bytea` de **comprimento zero** no
dump — coluna declarada, conteúdo nenhum. `employees.photo_path` aponta para um
caminho de rede de 1996 que não existe.

Nenhuma outra coluna se perdeu, e isso é **verificado, não afirmado**: a §8 de
`21_validacao_carga.sql` compara as colunas das duas pontas contra essa lista de
três e marca qualquer outra ausência como perda silenciosa. Foi assim que
`employees.title_of_courtesy` (Mr., Mrs., Dr.) voltou para o modelo depois de ter
sido esquecida na primeira versão.

### Uma regra que precisou afrouxar

O `CHECK` de `customers.customer_id` começou como `^[A-Z]{5}$` — cinco letras
maiúsculas, que é o formato dos 91 códigos da base. Está errado como regra:
`ALFKI` vem de *Alfreds Futterkiste*, e quando duas empresas dão as mesmas cinco
letras o desempate usual é trocar uma por dígito. O `CHECK` fecharia a porta para
um cadastro legítimo. Ficou `^[A-Z0-9]{5}$`: prende o comprimento, que é regra
real, e libera o desempate.

### Uma regra que quase virou invenção

O primeiro rascunho tinha `UNIQUE (product_name)`. Os 77 nomes do dump são
distintos, então a constraint passava — mas ela **não é regra do negócio**: nada
impede dois fornecedores de vender "Mozzarella". Foi trocada por
`UNIQUE (supplier_id, product_name)`, que é a regra defensável: *o mesmo
fornecedor não cadastra o mesmo produto duas vezes.*

O caso oposto está a duas tabelas de distância e serve de contraprova: em
`territories` **não** existe unique no nome, porque a base tem dois territórios
chamados "New York" (10019 e 10038) — os dois atendidos pelo **mesmo** vendedor,
Steven Buchanan. O nome se repete; o território, não. Mesmo critério, resultados
opostos — é o dado que decide, não o hábito.

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

A prova de que os dois preços são coisas diferentes são os mesmos **662 itens
(30,7%)** de `docs/01` §4.4: o preço da venda difere do catálogo atual.

O contra-exemplo ajuda a fixar: se eu tivesse guardado `product_name` dentro de
`order_items`, aí sim seria violação — o nome do produto depende só de
`product_id`.

### 3FN — nenhum campo comum determina outro campo comum

Se `orders` guardasse `customer_company_name`, haveria uma cadeia
`order_id → customer_id → company_name`: dependência transitiva, violação de
3FN. Bastaria o cliente mudar de razão social para os pedidos antigos passarem a
mentir. Por isso `orders` guarda **só** `customer_id`.

**A pergunta difícil:** e as seis colunas `ship_*` do pedido, que em 90% dos
casos são cópia literal do endereço do cliente?

Não violam a 3FN — e o motivo é preciso. Dependência funcional não é "os valores
costumam coincidir", é "conhecer A **determina** B". Conhecer o cliente **não**
determina o endereço de entrega daquele pedido, e o número depende de quantas
colunas se compara:

| Critério | Pedidos iguais ao cadastro | Diferentes |
|---|---:|---:|
| só `ship_address`, `ship_city`, `ship_country` | 782 (94,2%) | **48 (5,8%)** |
| as seis colunas `ship_*` | 748 (90,1%) | **82 (9,9%)** |

Pelo critério estrito — as seis colunas, que é o que "o endereço inteiro"
significa — são **82 pedidos, quase 10%**, que saíram para lugar diferente do
cadastro. Em qualquer um dos dois critérios a conclusão é a mesma: o endereço de
entrega é atributo do pedido, não do cliente.

O que existe ali é outra coisa, e é honesto declarar: **falta uma entidade**. O
modelo ideal teria os endereços do cliente como entidade própria, e o pedido
referenciaria qual foi usado. Não implementei porque exigiria inventar
identificadores de endereço e decidir o que fazer com os 82 divergentes — e
porque a decisão não muda nenhuma das 16 perguntas. Fica registrada como dívida
consciente.

**E quanto à BCNF?** As 11 tabelas também estão, mas a afirmação merece a
análise em vez do parêntese — porque o contraexemplo clássico se sustenta nos
dados desta base. `postal_code` determina `city` e `country` em **100% das
linhas**: são 86 CEPs distintos entre os 90 clientes com CEP, e **zero** casos de
um mesmo CEP em cidades diferentes. Se isso fosse dependência funcional,
`customers` não estaria em BCNF, porque `postal_code` não é chave candidata.

Mas não é — e o critério é o mesmo que resolveu o caso do endereço de entrega
logo acima: **dependência funcional é uma regra do domínio, não uma regularidade
da amostra.** CEP é reorganizado, cidade é desmembrada, e esta base não é
autoridade de endereçamento postal. Coincidir em 100% de 90 linhas não é
determinar.

---

## 3.1 Duas cardinalidades que a chave estrangeira não consegue expressar

Os relacionamentos de `docs/02` viraram 11 chaves estrangeiras. Mas chave
estrangeira só garante um lado: que **o filho aponta para um pai que existe**.
Ela não garante o outro, a **participação mínima** — que o pai tenha pelo menos
um filho.

São **11 chaves estrangeiras** para os 10 relacionamentos de `docs/02`, pelo
motivo já explicado lá: o N:N de ATUAÇÃO conta duas vezes. E duas cardinalidades
do diagrama caem no buraco da participação mínima:

- `PEDIDO contém ITEM DO PEDIDO (1,N)` — "pedido sem item não é venda, é
  formulário em branco". O `nw` aceitaria um `INSERT` em `orders` sem nenhum
  item.
- `REGIÃO agrupa TERRITÓRIO (1,N)` — "região sem território não existe como
  região".

Garantir isso no banco exigiria *trigger* de constraint postergada, verificando
no fim da transação. Não implementei: é peso desproporcional para o ganho, e
uma trigger mal escrita quebra a carga em lote. **Ficam declaradas como regra de
aplicação** — e essa é uma pergunta clássica de banca, que agora tem resposta
pronta em vez de improviso.

**O critério que decidiu os três casos acima**, em uma frase: normalizei tudo
que tinha dependência funcional real; deixei como está o que só parecia
redundante. Normalizar até doer é tão errado quanto não normalizar.

---

## 4. Índices: quatro entraram, seis foram recusados

Foram dez candidatos. Nenhum entrou sem `EXPLAIN` provando que o planejador o escolhe.

| Índice | Serve às perguntas | Plano medido |
|---|---|---|
| `orders (customer_id)` | 06, 10, 11 | Bitmap Index Scan |
| `orders (employee_id)` | 04, 15 | Bitmap Index Scan |
| `orders (order_date)` | 02, 08, 09, 16 | **Index Only Scan** |
| `order_items (product_id)` | 01, 07, 12 | Bitmap Index Scan |

**O que explica quase todas as recusas:** a base é minúscula. A maior tabela,
`orders`, ocupa **15 páginas de 8 kB**. Ler 15 páginas inteiras é barato, então o
planejador só troca a varredura por índice quando o filtro é bem seletivo.

Os seis recusados, por motivo:

- **`order_items (order_id)`** — redundante. A PK é `(order_id, product_id)` e
  começa por `order_id`, então ela mesma atende.

  Aqui cabe uma precisão que vale ponto na banca: **não** é verdade que um índice
  composto "só serve" para a busca que começa pela primeira coluna. Pela segunda
  ele continua utilizável — o PostgreSQL varre o índice inteiro. O que acontece é
  que isso costuma sair mais caro que ler a tabela, e por isso o planejador
  prefere o Seq Scan. Comprovado: removendo `order_items_product_idx` e
  desligando `enable_seqscan`, o banco usa a PK com `Index Cond` em `product_id`.
  A formulação correta é **"a PK cobre mal essa busca"**, não "não cobre" — e é
  isso que justifica o índice dedicado.
- **`orders (customer_id, order_date)`** — composto, criado para o caso clássico
  "últimos pedidos do cliente X". Ele **tem** um nicho, mas estreito, e a medição
  mostra exatamente onde:

  | Consulta | Plano |
  |---|---|
  | cliente com 30 pedidos, `LIMIT 5` | lê `orders_date_idx` ao contrário — ignora o composto |
  | cliente com 6 pedidos, `LIMIT 5` | usa `orders_customer_idx` e ordena depois — ignora o composto |
  | cliente com 6 pedidos, **`LIMIT 1`** | **usa o composto** |

  Ou seja: ele só ganha quando o filtro é muito seletivo *e* a consulta pede uma
  linha só. **Nenhuma das 16 perguntas de negócio tem essa forma**, então o custo
  de manter não se paga. Recusado por não servir a este projeto — não por ser
  inútil em geral.
- **`products (category_id)`, `territories (region_id)`,
  `employee_territories (territory_id)`** — essas tabelas ocupam **uma** página.
  Ler a página custa um acesso; ler o índice e depois a tabela custa dois.
- **`products (supplier_id)`** — dois motivos, e o primeiro é o interessante:
  a constraint `UNIQUE (supplier_id, product_name)` **já cria um índice**, e
  `supplier_id` é a primeira coluna dele, então outro índice seria duplicata.
  *Toda constraint UNIQUE vem com um índice embutido* — vale conferir o que já
  se tem antes de criar mais um. O segundo motivo é o de sempre: com a tabela em
  uma página, o planejador nem esse índice de brinde usa.

Em produção, com milhões de pedidos, vários desses passariam a valer a pena. A
decisão vale para **este** volume, e está registrada assim de propósito.

---

## 5. Quatro views, nenhuma decorativa

| View | Responde | Serve às perguntas |
|---|---|---|
| `vw_venda_item` | uma linha por produto vendido, com receita calculada | 01, 04, 07, 10, 11, 14, 16 |
| `vw_pedido_resumo` | uma linha por pedido: valor, itens e prazos | 02, 06, 13 |
| `vw_estoque_critico` | o que está abaixo do ponto de reposição | 05 |
| `vw_hierarquia_funcionarios` | a árvore da equipe, por **CTE recursiva** | 15 |

Elas existem porque o cálculo de receita —
`preço × quantidade × (1 − desconto)` — apareceria em 11 das 16 consultas, e
cálculo repetido é cálculo que uma hora sai diferente em algum lugar.

`vw_pedido_resumo` usa **`LEFT JOIN`** com `order_items`, e isso é consequência
direta da §3.1: como o banco aceita um pedido sem itens, uma junção interna o
faria desaparecer da view em silêncio — e o "uma linha por pedido" viraria
mentira justamente no caso anômalo que se quer enxergar. Com `LEFT`, o pedido
vazio aparece com 0 itens e R$ 0,00.

**Um detalhe que a banca pode cobrar.** A receita total pela view dá
**1.265.793,29**, e a soma sem arredondar dá **1.265.793,04**. A diferença de
R$ 0,25 é proposital: a view arredonda **cada item**, como faz uma nota fiscal,
onde toda linha tem um valor em centavos. Arredondar só no fim daria um total
que não bate com a soma das linhas impressas.

---

## 6. Reproduzir do zero

```bash
docker compose up -d
for f in 00_northwind_original 10_ddl 20_load 21_validacao_carga 30_indexes 40_views 50_evidencias; do
  docker compose exec -T postgres psql -U pi -d northwind -v ON_ERROR_STOP=1 -f /sql/$f.sql
done
```

O laço começa pelo dump: num clone novo o `docker compose up -d` já o carrega
sozinho (está montado em `docker-entrypoint-initdb.d`), mas em quem já tinha o
volume criado ele precisa rodar, senão a carga do `nw` não encontra o `public`.

O `-v ON_ERROR_STOP=1` não é enfeite: sem ele o `psql` continua depois de um erro
e ainda sai com código 0 — ou seja, a carga "passaria" com uma constraint
violada no meio. É essa flag que sustenta a afirmação da §2.

Os scripts são idempotentes: `10_ddl.sql` recria o schema do zero e `20_load.sql`
trunca antes de inserir. Rodar duas vezes dá o mesmo resultado.
