# 4. Análise exploratória e qualidade dos dados

## 4.1 Procedimento e inventário

A conferência foi realizada em 05/09/2026, diretamente no PostgreSQL, em uma transação somente leitura. O notebook existente foi revisado e seus resultados estruturais foram conferidos por consultas independentes: contagem exata de linhas, inspeção das 92 colunas, nulos, chaves, relações e faixas de valores. Os comandos selecionados e suas saídas aparecem ao longo desta seção.

A análise usa o schema **public**, que preserva a fonte. O schema **nw** contém a implementação relacional já iniciada, com 11 tabelas e 3.311 linhas. Suas decisões de implementação serão detalhadas na Entrega 2. Separar os schemas permite comparar a origem com o modelo proposto.

<!-- table:inventario -->

A soma é **3.362 linhas em 14 tabelas**. Esse número reúne tipos diferentes de registro; não corresponde ao número de vendas. Há 830 pedidos e 2.155 itens, com média de 2,60 itens distintos por pedido e intervalo de 1 a 25 itens.

**Consulta 1 — Período e clientes com pedido.**

<!-- query:resumo -->

O recorte vai de 04/07/1996 a 06/05/1998. Dos 91 clientes cadastrados, 89 aparecem em pedidos. Os demais podem ser estudados como clientes sem compra registrada nesse período.

<!-- page -->

# 4. Análise exploratória — valores e concentração

## 4.2 Valor e distribuição dos pedidos

**Consulta 2 — Total e distribuição por pedido.** Os campos são convertidos para decimal antes da multiplicação. O arredondamento é feito na apresentação do resultado, após a soma.

<!-- query:valores -->

O total é **1.265.793,04**, com ticket médio de **1.525,05** e mediana de **943,25**. A média maior que a mediana e o maior pedido de 16.387,50 indicam a influência de pedidos de valor elevado. Por isso, a mediana complementa a média na descrição do pedido típico.

## 4.3 Participação das categorias

**Consulta 3 — Valor agrupado pela categoria do produto.**

<!-- query:categorias -->

Beverages e Dairy Products somam **502.375,47**, aproximadamente **39,7%** do valor total. Essa concentração ajuda a identificar a participação comercial das categorias. Ela não mede lucro, pois os custos dos produtos não estão disponíveis.

<!-- page -->

# 4. Análise exploratória — período e dados ausentes

## 4.4 Distribuição temporal

<!-- table:anos -->

A tabela foi produzida pela consulta **anos**, disponível no script de evidências. **1996 e 1998 são anos parciais**: os registros de 1996 começam em julho; os de 1998 terminam em maio. Comparar seus totais com 1997 como se fossem anos completos produziria uma interpretação inadequada de crescimento. Análises futuras usarão meses comparáveis; a janela curta limita conclusões sobre sazonalidade.

## 4.5 Completude

Foram contados os nulos de cada coluna por meio de **count(*) − count(coluna)**. Onze das 92 colunas apresentam pelo menos um nulo. As tabelas vazias não permitem avaliar completude de registros.

<!-- table:nulos -->

Os nulos se concentram em informações de contato e endereço. Sem documentação adicional, não é possível distinguir automaticamente ausência de preenchimento de campo não aplicável. Não serão substituídos por valores inventados. O nulo em **employees.reports_to** representa o funcionário sem superior cadastrado, no topo da hierarquia observada.

**Consulta 4 — Data de envio e intervalo até o envio.**

<!-- query:envio -->

Há **21 pedidos sem data de envio registrada (2,53%)**. A média de 8,49 dias considera apenas os 809 pedidos com data de envio. Nenhum desses números informa quando o cliente recebeu a mercadoria ou comprova que os pedidos sem data nunca foram enviados.

<!-- page -->

# 4. Análise exploratória — integridade e validade

## 4.6 Identificadores e relacionamentos

A fonte possui **14 chaves primárias e 13 chaves estrangeiras**. A revisão não encontrou duplicidade de identificadores nas 14 tabelas nem referências órfãs nas 13 relações verificadas. Isso não descarta duplicidades de cadastro com identificadores diferentes, que exigiriam critérios adicionais de comparação de nomes e endereços.

**Consulta 5 — Exemplos de verificação de relacionamentos.**

<!-- query:integridade -->

Os três testes retornaram zero. A presença de itens em todos os pedidos também permite calcular o ticket usando os 830 pedidos da base, sem excluir pedidos vazios.

## 4.7 Faixas de valores e coerência temporal

**Consulta 6 — Valores fora das faixas adotadas e envio anterior ao pedido.**

<!-- query:dominios -->

Os preços dos itens variam de **2,00 a 263,50**, as quantidades de **1 a 130** e os descontos de **0% a 25%**. Não foram encontrados casos fora das regras testadas. O desconto inferior a 100% é uma regra deste projeto; o máximo observado de 25% não será transformado em limite obrigatório.

A fonte não possui restrições **CHECK**, apesar de já ter chaves e outras regras de integridade. O modelo proposto usa validações explícitas para impedir valores inválidos em novas cargas. Ausência de erro na amostra e existência de uma proteção no banco são verificações diferentes.

<!-- page -->

# 4. Análise exploratória — precisão e histórico

## 4.8 Valores decimais e arredondamento

Na fonte, preço e desconto dos itens são armazenados como **real**, um tipo aproximado. A documentação do PostgreSQL recomenda **numeric** para valores monetários que exigem exatidão [4]. A conversão permite calcular sobre valores decimais, mas não recupera uma precisão que a origem já tenha perdido.

A soma executada com ponto flutuante foi **1265793.038653364**; com conversão para decimal, **1265793.0395**. Ambas são apresentadas como 1.265.793,04 com duas casas decimais. Há outra diferença, independente do tipo: o momento do arredondamento.

**Consulta 7 — Arredondar a soma ou arredondar cada item.**

<!-- query:arredondamento -->

A diferença é **0,25**. Este relatório usa **arredondamento apenas no total**. As views já criadas no schema nw arredondam por item; por isso, a comparação futura precisa adotar a mesma regra nos dois bancos antes de avaliar equivalência. O valor maior não indica, por si só, perda de dados na migração.

## 4.9 Preço e endereço registrados no pedido

**Consulta 8 — Comparação do preço do item com o cadastro do produto.**

<!-- query:precos -->

Em **662 dos 2.155 itens (30,7%)**, o preço praticado difere do preço do catálogo. A diferença não comprova quando ou por que o preço mudou. Ela mostra por que o cálculo deve usar o preço do item, preservado no pedido, em vez de substituí-lo pelo preço cadastrado do produto.

O mesmo cuidado se aplica ao endereço. Ao comparar destinatário, endereço, cidade, região, CEP e país, os seis campos coincidem com o cadastro do cliente em **748 dos 830 pedidos**; em 82 há diferença. A igualdade foi comparada tratando nulos correspondentes como iguais. O endereço do pedido será preservado como informação daquele pedido, sem eliminar campos apenas porque repetem o cadastro atual.

## 4.10 Avaliação da base

A base é adequada às análises descritivas propostas: os relacionamentos conferem e não há violações nas faixas testadas. Os cuidados principais são tratar nulos conforme seu significado, manter os dados próprios do pedido, padronizar decimais e arredondamento e respeitar as limitações temporais e de cobertura do negócio.
