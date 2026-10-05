# 4. Análise exploratória e qualidade dos dados

## 4.1 Inventário

A exploração foi feita no schema **public**, que guarda a base original intocada, por consultas SQL e pelo notebook de perfilamento. São 14 tabelas e 92 colunas.

<!-- table:inventario -->

As 3.362 linhas misturam cadastros, pedidos e itens; o número que interessa ao negócio é outro: **830 pedidos e 2.155 itens**, em média 2,6 produtos por pedido.

**Consulta 1 — Período e clientes com pedido.**

<!-- query:resumo -->

Os pedidos vão de 04/07/1996 a 06/05/1998. Dos 91 clientes cadastrados, 89 compraram nesse período.

<!-- page -->

# 4. Análise exploratória — valores e concentração

## 4.2 Valor dos pedidos

**Consulta 2 — Total e distribuição por pedido.** Os valores são convertidos para decimal antes da multiplicação e arredondados só no resultado.

<!-- query:valores -->

O total registrado é **1.265.793,04**. O ticket médio (1.525,05) fica bem acima da mediana (943,25), porque alguns pedidos grandes, como o de 16.387,50, puxam a média para cima. Para descrever o pedido típico, a mediana é a medida mais fiel.

## 4.3 Participação das categorias

**Consulta 3 — Valor por categoria.**

<!-- query:categorias -->

Beverages e Dairy Products somam 502.375,47, cerca de **40% do valor**. É concentração de receita registrada, não de lucro, porque a base não tem custos.

<!-- page -->

# 4. Análise exploratória — período e dados ausentes

## 4.4 Distribuição no tempo

<!-- table:anos -->

**1996 e 1998 são anos incompletos**: os registros começam em julho de 1996 e terminam em maio de 1998. Comparar os totais anuais daria a falsa impressão de que 1997 foi um ano excepcional. Por isso, as análises do capítulo 13 trabalham com meses e trimestres e marcam os períodos parciais.

## 4.5 Completude

Onze das 92 colunas têm algum nulo, quase todas de contato e endereço.

<!-- table:nulos -->

Nenhum nulo foi preenchido com valor inventado. O nulo em employees.reports_to tem significado próprio: é o funcionário no topo da hierarquia.

**Consulta 4 — Data de envio e tempo até o envio.**

<!-- query:envio -->

**21 pedidos (2,53%) não têm data de envio.** A média de 8,49 dias considera só os 809 pedidos com data. A ausência não prova que o pedido não saiu, e nenhum desses números mede a entrega ao cliente.

<!-- page -->

# 4. Análise exploratória — integridade e validade

## 4.6 Chaves e relacionamentos

A base tem 14 chaves primárias e 13 chaves estrangeiras, sem identificadores duplicados nem referências órfãs.

**Consulta 5 — Verificação de relacionamentos.**

<!-- query:integridade -->

Todos os pedidos têm itens, então o ticket médio pode usar os 830 pedidos sem exclusões.

## 4.7 Faixas de valores

**Consulta 6 — Valores fora das faixas e envio antes do pedido.**

<!-- query:dominios -->

Preços vão de 2,00 a 263,50, quantidades de 1 a 130 e descontos de 0% a 25%, sem casos inválidos. A base original, porém, não tem nenhuma restrição CHECK: os dados estão corretos hoje, mas nada impede um valor inválido amanhã. O modelo relacional do projeto acrescenta essas regras (capítulo 6).

<!-- page -->

# 4. Análise exploratória — precisão e histórico

## 4.8 Decimais e momento do arredondamento

Na base original, preço e desconto são do tipo **real**, que guarda aproximações. Para dinheiro, o PostgreSQL recomenda **numeric** [4]. Converter evita novos erros, embora não recupere uma precisão que a origem já tenha perdido.

Também importa *quando* se arredonda.

**Consulta 7 — Arredondar a soma ou arredondar cada item.**

<!-- query:arredondamento -->

Arredondar cada item antes de somar acrescenta **0,25** ao total. Por isso, todo o projeto calcula com decimais exatos e arredonda apenas na apresentação. Essa regra se mostrou decisiva na comparação entre os bancos.

## 4.9 Preço e endereço pertencem ao pedido

**Consulta 8 — Preço do item comparado ao preço do catálogo.**

<!-- query:precos -->

Em **662 dos 2.155 itens (30,7%)**, o preço da venda é diferente do preço atual do catálogo. Com o endereço acontece o mesmo: em 82 dos 830 pedidos, o endereço de envio difere do cadastro do cliente. Conclusão: preço e endereço são fatos da venda e precisam ser guardados no pedido, não buscados no cadastro.

## 4.10 Avaliação

A base é adequada para análises descritivas: os relacionamentos fecham e os valores estão dentro das faixas. Os cuidados que guiaram o restante do projeto são quatro: respeitar o significado dos nulos, manter preço e endereço do pedido, calcular com decimais exatos e não tratar anos incompletos como completos.
