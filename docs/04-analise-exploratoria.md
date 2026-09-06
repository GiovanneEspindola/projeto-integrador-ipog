# 04 — Análise Exploratória e Qualidade dos Dados

> **Entrega 01** · Fase 2 do CRISP-DM
> Autor: Giovanne Espíndola · Data: 05/09/2026
>
> Todo número deste documento foi **executado** contra o banco. As saídas brutas
> estão versionadas em `apresentacao/evidencias/01-perfil-*.txt`, e os scripts
> que as geraram estão em `sql/01_exploracao.sql` e no notebook
> `etl/perfilamento.ipynb`.

---

Esta é a fase de **entendimento dos dados** do CRISP-DM. Ela tem duas metades,
e as duas estão aqui: primeiro **descrever** a base — o que ela contém, em que
volume, com que valores; depois **avaliar a qualidade** dela — o que está certo,
o que está errado, e o que é armadilha.

O resultado desta fase é o que justifica cada decisão de modelagem da Entrega 02.
Nenhuma correção feita lá é arbitrária: cada uma responde a um achado daqui.

---

## 1. Como a análise foi feita, e como reproduzi-la

```bash
# 1. baixar o dump original
curl -fsSL https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql \
  -o sql/00_northwind_original.sql

# 2. carregar no schema public (a FONTE, que fica intocada)
docker compose exec -T postgres psql -U pi -d northwind \
  -v ON_ERROR_STOP=1 -f /sql/00_northwind_original.sql

# 3. perfilamento estrutural (6 arquivos de evidência)
uv run jupyter nbconvert --to notebook --execute --inplace etl/perfilamento.ipynb

# 4. perfilamento de negócio (1 arquivo de evidência)
docker compose exec -T postgres psql -U pi -d northwind \
  -v ON_ERROR_STOP=1 -f /sql/01_exploracao.sql
```

A carga terminou com **exit code 0** e nenhum erro: 14 `CREATE TABLE`,
3362 `INSERT`, 27 `ALTER TABLE` de constraint. O dump escolhido não contém
`OWNER TO` nem `CREATE ROLE`, então carrega limpo em qualquer usuário — foi
por isso que ele foi preferido a outras versões do Northwind que circulam.

**Conferência cruzada:** o log da carga reporta 3362 linhas inseridas; a soma
de `count(*)` das 14 tabelas depois da carga dá exatamente **3362**. Nada se
perdeu no caminho.


---


## 2. A base em números

### 2.1 Inventário

Evidência: `apresentacao/evidencias/01-perfil-01-inventario.txt`

| tabela | linhas | colunas | papel |
|---|---:|---:|---|
| `order_details` | 2 155 | 5 | itens vendidos — **onde está o dinheiro** |
| `orders` | 830 | 14 | cabeçalho da venda |
| `territories` | 53 | 3 | subdivisão comercial |
| `us_states` | 51 | 4 | tabela de apoio **sem nenhuma FK apontando para ela** |
| `employee_territories` | 49 | 2 | associativa funcionário ↔ território |
| `customers` | 91 | 11 | clientes empresariais |
| `products` | 77 | 10 | catálogo |
| `suppliers` | 29 | 12 | fornecedores |
| `employees` | 9 | 18 | equipe de vendas |
| `categories` | 8 | 4 | classificação de produto |
| `shippers` | 6 | 3 | transportadoras |
| `region` | 4 | 2 | região comercial |
| `customer_demographics` | **0** | 2 | **vazia** |
| `customer_customer_demo` | **0** | 2 | **vazia** |
| **total** | **3 362** | **92** | |

A base é **pequena** — 3362 linhas, poucas centenas de kilobytes. Isso tem uma
consequência que este trabalho precisa assumir desde já e está registrada na
seção de limitações do benchmark: **não dá para medir escalabilidade aqui.**
O que se pode medir é sobrecarga por consulta e diferença de modelo, não
comportamento sob volume.

### 2.2 Período e volume

Evidência: seções 1 e 2 de `01-perfil-07-exploracao-negocio.txt`

| | |
|---|---|
| Primeiro pedido | **1996-07-04** |
| Último pedido | **1998-05-06** |
| Janela de operação | **671 dias** (~22 meses) |
| Pedidos | **830** |
| Clientes que compraram | **89** de 91 cadastrados |
| Vendedores ativos | **9** de 9 |

| ano | pedidos | clientes distintos | receita |
|---|---:|---:|---:|
| 1996 | 152 | 67 | 208 083,97 |
| 1997 | 408 | 86 | 617 085,20 |
| 1998 | 270 | 81 | 440 623,87 |

1996 e 1998 são **anos parciais** (a base começa em julho de 1996 e termina em
maio de 1998). Comparar o total de 1996 com o de 1997 como se fosse queda ou
crescimento seria erro de leitura — é a janela que é diferente. Só 1997 é ano
cheio.

### 2.3 Dinheiro

Evidência: seções 3, 4, 5, 6 e 7 de `01-perfil-07-exploracao-negocio.txt`

| | |
|---|---|
| **Receita total do período** | **1 265 793,04** |
| Ticket médio | 1 525,05 |
| **Mediana** do pedido | **943,25** |
| Menor pedido | 12,50 |
| Percentil 95 | 4 706,62 |
| Maior pedido | 16 387,50 |
| Itens por pedido (mín / médio / máx) | 1 / 2,60 / 25 |

A média (1 525,05) é **62% maior que a mediana** (943,25). Isso é a assinatura
de uma distribuição com cauda longa à direita: a maioria dos pedidos é pequena e
poucos pedidos muito grandes puxam a média para cima. Em uma apresentação, citar
a média sozinha superestima o pedido típico — a mediana descreve melhor.

**Receita por categoria** — as 8 categorias, com participação:

| categoria | produtos | receita | % |
|---|---:|---:|---:|
| Beverages | 12 | 267 868,18 | 21,2% |
| Dairy Products | 10 | 234 507,29 | 18,5% |
| Confections | 13 | 167 357,23 | 13,2% |
| Meat/Poultry | 6 | 163 022,36 | 12,9% |
| Seafood | 12 | 131 261,74 | 10,4% |
| Condiments | 12 | 106 047,09 | 8,4% |
| Produce | 5 | 99 984,58 | 7,9% |
| Grains/Cereals | 7 | 95 744,59 | 7,6% |

Duas categorias (Beverages + Dairy) fazem **39,7%** da receita. Meat/Poultry
chama atenção pelo inverso: só **6 produtos** geram 12,9% — é a categoria de
maior receita por item de catálogo.

**Receita por país do cliente** (top 5): USA 245 584,61 · Germany 230 284,63 ·
Austria 128 003,84 · Brazil 106 925,78 · France 81 358,32. Os dois primeiros
somam **37,6%** — a Northwind é uma operação concentrada em dois mercados.

---


---


## 3. Avaliação da qualidade — o que está errado

Esta seção é o coração da justificativa para o schema `nw`. Cada item traz a
evidência que o comprova.

### 3.1 Dinheiro em ponto flutuante — o erro mais grave

`order_details.unit_price`, `order_details.discount`, `orders.freight` e
`products.unit_price` são do tipo **`real`** (ponto flutuante de 4 bytes).

Ponto flutuante binário **não representa exatamente** valores decimais como
0,05 ou 19,90 — pelo mesmo motivo que 1/3 não tem representação decimal finita.
O erro é minúsculo em cada valor, mas soma-se ao longo da agregação.

A mesma soma, feita nos dois tipos (seção 3 da evidência):

```
  receita_em_real  | receita_em_numeric |  diferenca
-------------------+--------------------+-------------
 1265793.038653364 |       1265793.0395 | -0.00084664
```

Menos de um centavo em 1,2 milhão. **O ponto não é o tamanho do erro, é a
existência dele:** o valor em `real` nem sequer é estável — depende da ordem em
que as linhas foram somadas. Num sistema financeiro real isso é inaceitável, e
é o tipo de detalhe que separa quem copiou um dump de quem leu o schema.

**Decisão para o `nw`:** `numeric(10,2)` para valores monetários e
`numeric(4,3)` para desconto.

### 3.2 Nenhuma regra de negócio no banco

Evidência: `01-perfil-03-chaves-e-constraints.txt`

| tipo de constraint | quantidade |
|---|---:|
| PRIMARY KEY | 14 |
| FOREIGN KEY | 13 |
| **UNIQUE** | **0** |
| **CHECK** | **0** |
| índices além dos de PK | **0** |

A base tem integridade **referencial** (as FKs existem e, verificado por
anti-join, **nenhuma das 13 tem um único registro órfão**), mas **nenhuma
integridade de domínio**. Hoje o banco aceitaria, sem reclamar:

- quantidade vendida **negativa**
- desconto de **300%**
- preço unitário **negativo**
- `discontinued = 7`
- um pedido **enviado antes de ter sido feito**

Os dados atuais não violam nada disso — conferido na seção 17 da evidência,
todas as sete faixas verificadas têm **0 violações**, e não há nenhuma data fora
de ordem. Mas isso é sorte da carga, não garantia do modelo. **A constraint não
existe para descrever o que os dados são; existe para impedir o que eles não
podem virar.**

Faixas reais medidas, que fundamentam os CHECK do `nw`:

| coluna | mínimo | máximo | CHECK proposto |
|---|---:|---:|---|
| `order_details.unit_price` | 2,00 | 263,50 | `>= 0` — zero registra brinde e amostra |
| `order_details.quantity` | 1 | 130 | `> 0` |
| `order_details.discount` | 0,00 | 0,25 | `>= 0 AND < 1` |
| `orders.freight` | 0,02 | 1 007,64 | `>= 0` |
| `products.units_in_stock` | 0 | 125 | `>= 0` |
| `products.discontinued` | 0 | 1 | vira `boolean` |

### 3.3 Ausência de índice em toda coluna de junção

Os únicos 14 índices da base são os criados automaticamente pelas PKs. Nenhuma
FK tem índice. Consequência prática: `order_details.order_id` — a coluna mais
usada do banco, presente em toda consulta de faturamento — **não tem índice**,
e todo `JOIN` sobre ela varre a tabela inteira.

Cardinalidade medida das principais colunas de junção
(`01-perfil-05-cardinalidade-juncoes.txt`):

| junção | linhas | distintos | média filhos/pai | seletividade |
|---|---:|---:|---:|---|
| `order_details.order_id → orders` | 2 155 | 830 | 2,6 | **alta** — bom candidato a índice |
| `order_details.product_id → products` | 2 155 | 77 | 28,0 | média |
| `orders.customer_id → customers` | 830 | 89 | 9,3 | alta |
| `orders.employee_id → employees` | 830 | 9 | 92,2 | **baixa** — índice pode não ser usado |
| `orders.ship_via → shippers` | 830 | 3 | 276,7 | **muito baixa** |
| `products.category_id → categories` | 77 | 8 | 9,6 | baixa |

Isso não significa "crie índice em tudo". `orders.ship_via` tem **3 valores
distintos em 830 linhas** — um índice ali provavelmente seria ignorado pelo
planejador, porque ler o índice e depois buscar 276 linhas na tabela é mais caro
que varrer as 830 direto. Essa distinção é exatamente o que o `nw` precisa
justificar índice a índice.

### 3.4 Redundância intencional vs. redundância acidental

Esta é a distinção que mais rende em banca, e a base tem um exemplo perfeito de
cada lado.

**Intencional — e correta.** `order_details.unit_price` repete um dado que já
existe em `products.unit_price`. Parece violação de normalização. Não é: é um
**snapshot histórico**. O preço de catálogo muda; o preço pelo qual a venda
aconteceu não pode mudar nunca — senão o faturamento do ano passado se altera
sozinho quando alguém reajusta a tabela de preços.

A prova está nos dados (seção 12 da evidência): **662 dos 2155 itens (30,7%)
têm preço de venda diferente do preço de catálogo atual.** Exemplo real:

| produto | preço no catálogo hoje | preço cobrado na venda | data da venda |
|---|---:|---:|---|
| Alice Mutton | 39,00 | 31,20 | 1996-07-25 |

Se `order_details` não guardasse o próprio preço, todo o histórico de receita
seria recalculado a 39,00 e estaria errado.

**Acidental — e discutível.** `orders` guarda o endereço de entrega em seis
colunas soltas: `ship_name`, `ship_address`, `ship_city`, `ship_region`,
`ship_postal_code`, `ship_country`. Medido (seção 14):

- em **796 dos 830** pedidos (95,9%) o `ship_name` é idêntico ao
  `company_name` do cliente
- em **782 dos 830** (94,2%) `ship_address`, `ship_city` e `ship_country` são
  cópia literal do cadastro. Comparando as **seis** colunas `ship_*` — somando
  `ship_name`, `ship_region` e `ship_postal_code` — a coincidência cai para
  **748 (90,1%)**

Aqui a justificativa de snapshot é **fraca**: endereço de entrega não é um valor
que precise ser congelado por razão contábil, e 90% do conteúdo é duplicação
pura. Ainda assim, **48 pedidos (5,8%)** têm endereço de entrega diferente do
cadastro pelo critério das três colunas, e **82 (9,9%)** pelo critério das seis —
ou seja, a coluna não é inútil, ela cobre o caso de entrega em endereço
alternativo.

**A resposta madura não é "normalizar" nem "deixar como está":** é reconhecer
que faltou uma entidade. O modelo correto teria endereços do cliente como
entidade própria, com o pedido referenciando qual endereço foi usado.

### 3.5 Um N:N que os dados desmentem

`employee_territories` tem PK composta `(employee_id, territory_id)` — a
estrutura clássica de um relacionamento muitos-para-muitos. Os dados dizem
outra coisa (seção 9):

```
 vinculos | funcionarios_com_territorio | territorios_vinculados | max_funcionarios_por_territorio
----------+-----------------------------+------------------------+---------------------------------
       49 |                           9 |                     49 |                               1
```

São 49 vínculos para 49 territórios distintos, e **nenhum território tem mais de
um funcionário**. Na prática o relacionamento é **1:N** (um funcionário atende
vários territórios, cada território tem um único responsável), não N:N.

Isso não é necessariamente erro de modelagem — pode ser uma escolha deliberada
de permitir N:N para o futuro. Mas é uma pergunta que a banca pode fazer, e a
resposta precisa vir com o número na mão. Além disso, **4 dos 53 territórios não
têm nenhum funcionário** — buraco de cobertura comercial.

### 3.6 Colunas de chave estrangeira que aceitam nulo

`orders.customer_id`, `orders.employee_id`, `orders.ship_via` e
`orders.order_date` são todas **nullable**. Ou seja, o schema atual permite um
pedido **sem cliente, sem vendedor, sem transportadora e sem data**. Nos dados
carregados nenhuma dessas colunas tem nulo — mas, de novo, isso é o estado
atual, não uma garantia.

`orders.shipped_date` nulo, por outro lado, é **legítimo e significativo**: os
21 pedidos com `shipped_date IS NULL` são pedidos que nunca foram enviados. Aqui
o nulo carrega informação de negócio e deve continuar permitido.

### 3.7 Tipos frouxos e outros achados

| achado | evidência | impacto |
|---|---|---|
| `order_id` é `smallint` (teto 32 767) | maior id atual: **11 077**, folga de 21 690 | limite de crescimento embutido no tipo |
| `discontinued` é `integer` usado como booleano | valores observados: só 0 e 1 | `boolean` expressa a intenção |
| `customer_id` é `varchar(5)` — chave natural | 91 valores, todos com 5 letras | acopla o identificador ao nome da empresa |
| `products.quantity_per_unit` é texto livre | ex.: "10 boxes x 20 bags" | não é consultável nem calculável |
| `us_states` (51 linhas) **sem nenhuma FK** | `01-perfil-03` | tabela ilha, não conectada ao modelo |
| `customer_demographics` e `customer_customer_demo` **vazias** | 0 linhas | estrutura sem dado; N:N morto |
| `region` com nome genérico | 4 linhas | colide com a coluna `region`, que existe em quatro tabelas |

### 3.8 Nulos concentrados em colunas de endereço

Evidência: `01-perfil-04-nulos-por-coluna.txt` — de 92 colunas, **11 têm nulo**.

| coluna | % nulo | leitura |
|---|---:|---|
| `suppliers.homepage` | 82,8% | base de 1996: quase ninguém tinha site |
| `suppliers.region` | 69,0% | "region" só faz sentido em países federativos |
| `customers.region` | 65,9% | idem |
| `orders.ship_region` | 61,1% | idem, herdado do cliente |
| `suppliers.fax` | 55,2% | nem toda empresa tinha fax |
| `employees.region` | 44,4% | 4 dos 9 funcionários são do escritório de Londres |
| `customers.fax` | 24,2% | |
| `orders.shipped_date` | 2,5% | **21 pedidos nunca enviados — informação real** |
| `orders.ship_postal_code` | 2,3% | |
| `customers.postal_code` | 1,1% | |
| `employees.reports_to` | 11,1% | **1 nulo: o topo da hierarquia** |

Dois desses nulos **não são falta de dado, são dado**: `reports_to` nulo
identifica o presidente, e `shipped_date` nulo identifica pedido não enviado.
Os demais são o que se chama de *nulo por inaplicabilidade* — "região" não se
aplica a um endereço na Alemanha.

---


---


## 4. Avaliação da qualidade — o que está certo

Um relatório que só aponta defeito é tão desequilibrado quanto um que só elogia.
O Northwind acerta em coisas importantes:

- **Integridade referencial impecável.** As 13 FKs foram testadas por anti-join
  e **nenhuma tem um único órfão**. Nenhum item de pedido aponta para pedido
  inexistente, nenhum produto aponta para categoria inexistente.
- **Nenhum pedido vazio.** Os 830 pedidos têm pelo menos um item.
- **Nenhum produto encalhado no cadastro.** Todos os 77 produtos foram vendidos
  ao menos uma vez; todos os 29 fornecedores têm produto vendido.
- **Coerência temporal perfeita.** Zero pedidos enviados antes da data do
  pedido, zero prazos anteriores ao pedido, zero pedidos sem data.
- **PK composta onde deve.** `order_details(order_id, product_id)` e
  `employee_territories(employee_id, territory_id)` estão corretas.
- **O auto-relacionamento funciona.** A hierarquia de `reports_to` é consistente:
  Andrew Fuller (VP de Vendas) no topo com 5 subordinados diretos, Steven
  Buchanan (Gerente) com 3 — **três níveis**, sem ciclo.

---


---


## 5. Limitações declaradas

1. **Volume.** 830 pedidos e 2155 itens. Qualquer consulta roda em milissegundos
   nos dois bancos. O benchmark da Entrega 04 mede **sobrecarga por consulta e
   diferença de modelo**, não escalabilidade.
2. **Recorte temporal.** 1996 e 1998 são anos parciais; só 1997 é ano cheio.
3. **Sem margem.** Sem custo de produto, toda análise de rentabilidade é sobre
   receita, não lucro.
4. **Duas tabelas vazias.** `customer_demographics` e `customer_customer_demo`
   não sustentam nenhuma análise.
5. **Dados sintéticos.** O Northwind é uma base de demonstração da Microsoft,
   não um extrato de operação real. Padrões encontrados descrevem o dataset, não
   o mercado de alimentos dos anos 90.

---

---

## 6. O que esta fase entrega para a próxima

A análise exploratória fecha com um diagnóstico em uma frase: **o Northwind tem
integridade referencial impecável e integridade de domínio inexistente.** As
chaves estrangeiras estão todas corretas e sem órfãos; as regras de negócio não
existem no banco — nada impede quantidade negativa, desconto de 300% ou pedido
enviado antes de ser feito.

Isso define a agenda da **fase 3 do CRISP-DM (preparação dos dados)**, na
Entrega 02, que enfrentará um a um os achados da seção 3:

| Achado desta fase | O que a preparação vai fazer |
|---|---|
| dinheiro em ponto flutuante (3.1) | converter para tipo decimal exato |
| nenhuma regra de negócio no banco (3.2) | declarar as restrições de domínio, com as faixas medidas aqui |
| nenhum índice nas colunas de junção (3.3) | criar índice onde a cardinalidade medida justifica — e **só** onde justifica |
| redundância acidental de endereço (3.4) | decidir entre normalizar e preservar, com o número na mão |
| N:N que os dados desmentem (3.5) | manter a estrutura, documentando o que os dados dizem |
| chaves estrangeiras que aceitam nulo (3.6) | tornar obrigatório o que é obrigatório — preservando o nulo que é informação |
| tipos frouxos (3.7) | tipos que expressam a intenção; descartar as tabelas mortas |
