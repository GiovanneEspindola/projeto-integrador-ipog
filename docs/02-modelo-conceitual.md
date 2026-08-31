# 02 — Modelo Conceitual (ER) do Northwind

> **Entrega 01** · Projeto Integrador Área 03 — Banco de Dados (IPOG)
> Autor: Giovanne Espíndola · Data: 30/08/2026
>
> Diagrama: `docs/diagramas/er-conceitual.drawio` · exportação: `docs/diagramas/er-conceitual.png`
> Cada cardinalidade abaixo vem acompanhada do número que a sustenta, medido em
> `apresentacao/evidencias/01-perfil-05-cardinalidade-juncoes.txt` e reconferido
> por `etl/valida_conceitual.py`.

---

## 1. O arquivo do diagrama

O diagrama está em formato **`.drawio`** — XML nativo do draw.io (diagrams.net).
Duas consequências práticas: ele abre e continua editável no aplicativo, e é
texto, então versiona no Git como qualquer outro arquivo de código (um `git diff`
mostra que uma cardinalidade mudou).

Para abrir: <https://app.diagrams.net> → *Open Existing Diagram*, ou a extensão
**Draw.io Integration** no VS Code, que abre o arquivo direto no editor.

O diagrama não é só desenho: `etl/valida_conceitual.py` confere cada afirmação
dele contra o banco — as 11 entidades e seus atributos existem no schema
`public`, os identificadores batem com as chaves primárias reais, as 11
cardinalidades conferem com as junções medidas, e as 14 tabelas da base estão
todas classificadas (11 modeladas, 3 excluídas com motivo). O script sai com
código 1 se qualquer verificação falhar, e a saída fica em
`apresentacao/evidencias/02-validacao-er-conceitual.txt`.

```bash
uv run python etl/valida_conceitual.py
```

---

## 2. As onze entidades, em três blocos

O modelo é mais fácil de defender se apresentado em blocos, não como uma lista
de onze caixas.

**Bloco 1 — o que a empresa vende.** `FORNECEDOR` vende `PRODUTO`, e cada
produto pertence a uma `CATEGORIA`. É o catálogo.

**Bloco 2 — a venda.** `CLIENTE` faz `PEDIDO`, e o pedido é composto de
`ITEM DO PEDIDO`, um por produto vendido. É a transação.

**Bloco 3 — quem vende e quem entrega.** `FUNCIONÁRIO` registra o pedido,
`TRANSPORTADORA` entrega. Funcionários atuam em `TERRITÓRIO` (pela entidade
associativa `ATUAÇÃO`), e territórios se agrupam em `REGIÃO`. É a operação.

O modelo é conceitual: tem entidades, relacionamentos, cardinalidades e os
atributos que identificam ou descrevem cada entidade. **Não tem** tipo de dado,
chave estrangeira, índice nem tabela de junção física — isso é assunto do modelo
lógico, em `docs/04`.

---

## 3. Justificativa de cada cardinalidade

A notação é pé-de-galinha. `(1,1)` é "exatamente um", `(0,1)` "zero ou um",
`(1,N)` "um ou muitos", `(0,N)` "zero ou muitos".

| Relacionamento | Cardinalidade | Regra de negócio que a justifica | Evidência medida |
|---|---|---|---|
| CLIENTE **faz** PEDIDO | (1,1) — (0,N) | Todo pedido é de alguém; um cliente cadastrado pode ainda não ter comprado | 830 pedidos, nenhum sem cliente · **89 dos 91** clientes têm pedido: 2 nunca compraram |
| FUNCIONÁRIO **registra** PEDIDO | (1,1) — (0,N) | Toda venda tem um responsável; um recém-contratado ainda não vendeu | 9 de 9 funcionários com pedido · média de **92,2** pedidos por funcionário |
| TRANSPORTADORA **entrega** PEDIDO | (1,1) — (0,N) | O pedido sai por uma transportadora; nem toda transportadora cadastrada é usada | apenas **3 das 6** transportadoras aparecem (50%) |
| PEDIDO **contém** ITEM DO PEDIDO | (1,1) — (1,**N**) | Pedido sem nenhum item não é uma venda — é um formulário em branco | 2155 itens em 830 pedidos, média **2,6** · os 830 pedidos têm item, nenhum vazio |
| PRODUTO **é vendido em** ITEM DO PEDIDO | (1,1) — (0,N) | Um produto do catálogo pode nunca ter sido vendido | 77 de 77 produtos vendidos, média **28** itens por produto |
| CATEGORIA **classifica** PRODUTO | (1,1) — (0,N) | Todo produto tem categoria; categoria nova pode estar vazia | 8 categorias, média **9,6** produtos |
| FORNECEDOR **fornece** PRODUTO | (1,1) — (0,N) | Todo produto tem origem; fornecedor pode estar sem produto ativo | 29 fornecedores, média **2,7** produtos |
| REGIÃO **agrupa** TERRITÓRIO | (1,1) — (1,N) | Região comercial sem nenhum território não existe como região | 4 regiões, 53 territórios, média **13,2**, todas com território |
| FUNCIONÁRIO **atua em** TERRITÓRIO | (0,N) — (0,N) | Um funcionário cobre vários territórios; um território pode ter mais de um responsável | 49 vínculos · 9 funcionários, média **5,4** territórios cada · **4 dos 53** territórios sem ninguém |
| FUNCIONÁRIO **chefia** FUNCIONÁRIO | (0,1) — (0,N) | Cada um responde a no máximo um superior; o topo não responde a ninguém | 9 funcionários, **1 sem chefe** (o topo) e **2** chefes distintos |

O padrão `(1,1) — (0,N)` domina a tabela, e a leitura é sempre a mesma: **o lado
filho é obrigatório, o lado pai é opcional.** Um pedido tem que ter cliente; um
cliente não tem que ter pedido.

Um detalhe que a banca pode cobrar: cinco dessas colunas de junção
(`orders.customer_id`, `orders.employee_id`, `orders.ship_via`,
`products.supplier_id`, `products.category_id`) são **nuláveis no dump original**,
embora não tenham nenhum nulo nos dados. O modelo conceitual as trata como
obrigatórias porque a regra de negócio é obrigatória — o dump é permissivo, o
negócio não é. É exatamente esse aperto que o schema `nw` vai transformar em
`NOT NULL`.

---

## 4. As três decisões do modelo, e o que foi descartado

### 4.1 ITEM DO PEDIDO é entidade, não atributo de PEDIDO

**Descartado:** guardar os produtos vendidos dentro do próprio pedido, em campos
repetidos (`produto_1`, `produto_2`, …) ou numa lista.

**Por quê:** um pedido tem número variável de produtos — na base, de 1 a dezenas.
Campo repetido obriga a fixar um teto arbitrário e viola a 1FN. Separar em
entidade própria é o que permite perguntar "quanto vendemos deste produto"
sem varrer coluna por coluna.

A identificação de `ITEM DO PEDIDO` é **composta**: o par (pedido, produto). Não
existe item fora de um pedido, e o mesmo produto não aparece duas vezes no mesmo
pedido — a chave composta impõe as duas regras de uma vez.

### 4.2 ATUAÇÃO é N:N na estrutura, mesmo os dados dizendo 1:N

Os dados medidos: **49 vínculos para 49 territórios distintos**, nenhum
território com mais de um responsável. Na prática, hoje, o relacionamento é 1:N.

**Descartado:** simplificar para 1:N, colocando o responsável dentro de
`TERRITÓRIO`.

**Por quê:** a assimetria de custo. Suportar o N:N custa uma entidade
associativa. Não suportar custa uma migração de schema no dia em que dois
vendedores dividirem uma praça — o que é uma decisão comercial trivial, não uma
mudança de negócio. Modelar para o caso mais geral, quando o custo é uma tabela,
é a escolha defensável.

Isto é material de banca: a pergunta "por que N:N se os dados são 1:N?" tem
resposta pronta, com o número na mão.

### 4.3 Três tabelas ficaram de fora

`customer_demographics` e `customer_customer_demo` existem na base original e
estão **vazias — 0 linhas as duas**.

**Descartado:** incluí-las no modelo "porque estão no dump".

**Por quê:** entidade sem nenhuma instância não descreve o domínio, descreve uma
intenção que nunca virou dado. Modelo conceitual é retrato do negócio que
existe.

A terceira é `us_states`, e o motivo é outro: ela tem **51 linhas**, mas
**nenhuma chave estrangeira aponta para ela** — as colunas `region` de
`customers`, `employees` e `suppliers` são texto livre, não referência. É uma
lista de apoio geográfico que veio junto no dump, não uma entidade do negócio de
distribuição.

As três exclusões ficam **declaradas** no próprio diagrama, numa nota — o
avaliador vê que foi decisão, não descuido.

---

## 5. O que este modelo deliberadamente não mostra

Tipo de dado, tamanho de campo, chave estrangeira, índice, constraint, tabela
física de junção. Tudo isso é modelo lógico e físico, e entra em `docs/04` junto
com o schema `nw`.

A separação não é formalismo: o modelo conceitual é o documento que se discute
com quem entende do negócio e não entende de banco. No momento em que aparece
`VARCHAR(40)` no diagrama, essa conversa acaba.

---

## 6. Próximo passo

Plano Híbrido (`docs/03`) e schema `nw` (`docs/04`), onde cada cardinalidade
desta tabela vira uma chave estrangeira e cada regra de negócio citada aqui vira
uma constraint verificável.
