# 12. Contrato analítico e método

A Entrega 3 responde a 16 perguntas com consultas SQL e pipelines MongoDB equivalentes. A comparação usa os dados do Northwind conferidos em 22/09/2026 e novamente em 24/09/2026: 830 pedidos, 2.155 itens, 91 clientes e 77 produtos. A reconstrução das 3.311 linhas relacionais foi repetida sem divergências. Os scripts completos estão nos apêndices deste documento.

## 12.1 Regras compartilhadas

O período padrão é **[01/07/1996, 01/06/1998)**: início incluído e fim excluído. Ele contém todos os pedidos disponíveis, de 04/07/1996 a 06/05/1998. As séries mensais incluem os 23 meses do intervalo. Julho de 1996 e maio de 1998 têm cobertura parcial dos registros.

Valor significa **preço praticado × quantidade × (1 − desconto)**, sem frete. Todos os cálculos monetários usam numeric ou Decimal128. Somatórios são comparados sem arredondamento; médias e percentuais admitem diferença absoluta máxima de 0,000000000001, devido às divisões com expansão decimal. Numeradores e denominadores também são conferidos. Na exibição, os valores usam duas casas e ROUND_HALF_UP. As implementações não dependem de igual comportamento de round e $round [4, 11].

O total exato é **1265793.03950**. Arredondar somente ao final resulta em **1.265.793,04**; somar itens previamente arredondados resulta em **1.265.793,29**. As views históricas permanecem preservadas. As novas consultas monetárias usam o schema **nw_analytics**, sem arredondamento intermediário.

Ticket é valor dos pedidos dividido pelo número de pedidos. Um pedido com vários itens conta uma única vez. Identificadores definem os grupos; nomes servem para apresentação. A ordenação final é explícita nos dois bancos e também foi validada.

## 12.2 Recência, ranking e limites

Inatividade e RFM consideram todo o histórico até **06/05/1998**, inclusive, independentemente da janela mensal. O corte de seis meses é **06/11/1997**. Última compra anterior ao corte significa inatividade; compra no próprio corte não. Clientes sem compras formam uma categoria própria.

O ranking retorna até cinco produtos por categoria, com valor decrescente e ID crescente no desempate. A curva ABC considera a participação acumulada anterior ao cliente: classe A abaixo de 80%, B abaixo de 95%, C nos demais casos. O cliente que cruza o limite completa a classe em que entrou. Clientes sem compras ficam fora dessas classes.

RFM recebe faixas didáticas fixas, sem ajuste preditivo. R: até 30 dias = 3, até 90 = 2, acima = 1. F: pelo menos 10 pedidos = 3, pelo menos 5 = 2, abaixo = 1. M: pelo menos 10.000 unidades monetárias = 3, pelo menos 5.000 = 2, abaixo = 1. Sem compras: R, F e M recebem zero; recência permanece nula. Essas faixas são uma convenção de segmentação, não um padrão universal nem recomendação validada de marketing.

Estoque é o estado cadastrado, sem reconstrução histórica. Data de envio ausente significa ausência de registro, não prova de que o pedido nunca saiu. O intervalo até envio não é tempo de entrega. A base não permite calcular lucro, margem ou recebimento financeiro. A distribuição trimestral não demonstra sazonalidade recorrente.

## 12.3 Contratos de saída

Cada arquivo QNN.sql tem um PNN.js correspondente. As consultas são executáveis com o recorte padrão escrito no código; alterar um parâmetro exige atualizar as duas pontas e repetir a conferência. Q05 usa o estoque cadastrado; Q06 e Q11 usam a referência histórica indicada acima.

As saídas monetárias são decimais; IDs, contagens, quantidades e dias são inteiros, embora somas SQL de contagens possam ser representadas por numeric. Datas de resultado usam AAAA-MM-DD. Valores indefinidos são null nos dois bancos. As tabelas do relatório mostram a mesma saída validada, com formatação aplicada somente depois da comparação.

| Pares | Unidade de cada linha e ordenação |
|---|---|
| 01 e 14 | Categoria com movimento; ID da categoria crescente |
| 02, 08 e 09 | Mês do calendário; mês crescente, incluindo meses sem pedidos |
| 03 | Produto sem venda no período; ID do produto crescente |
| 04 | Funcionário cadastrado, inclusive sem pedidos; ID crescente |
| 05 | Categoria com produto abaixo do ponto; ID da categoria crescente; lista de produtos ordenada |
| 06 | Cliente inativo ou sem compras; código crescente |
| 07 | Produto classificado dentro da categoria; categoria e posição crescentes |
| 10 | Todos os clientes; valor decrescente, código crescente |
| 11 | Todos os clientes; código crescente |
| 12 | Par de produtos com pelo menos uma compra conjunta; contagem decrescente, IDs crescentes |
| 13 | Transportadora cadastrada, inclusive sem pedidos; ID crescente |
| 15 | Funcionário considerado como responsável por sua própria equipe; ID crescente |
| 16 | Trimestre com movimento, total e categorias; ano/trimestre/ID, com total antes das categorias |

## 12.4 Validação

Os 16 pares foram comparados linha a linha e campo a campo, sem reordenar os resultados depois da execução. A comparação também exige tipos compatíveis: inteiros e decimais são aceitos, mas ponto flutuante, valores lógicos trocados por números e datas fora da meia-noite UTC são rejeitados. Foram conferidos também os totais por mês, categoria e funcionário, as contagens de pedidos e a identidade bruto − desconto = valor líquido. O retorno vazio de produtos nunca vendidos foi preservado.

Como SQL e MongoDB poderiam compartilhar o mesmo erro de interpretação, os resultados também foram recalculados por um terceiro caminho, em Python, diretamente sobre as linhas de nw, com igualdade nos 16 pares.

Foram concluídas ainda **38 verificações adicionais** em dados sintéticos isolados: 16 pares com quatro pedidos de fronteira, 16 pares sem nenhum pedido, empate no ranking, empate de meio centavo no arredondamento, três rejeições de parâmetros inválidos e uma conferência conjunta das três procedures. Nos pedidos de fronteira, além da igualdade entre os bancos, 15 pares foram comparados com valores esperados calculados à mão, por exemplo: mês sem vendas com ticket nulo, percentual nulo após mês com valor zero, compra exatamente no corte de inatividade (fora da lista) e um dia antes (dentro), média de envio que ignora a data ausente e suporte de 25% para o único par em quatro pedidos. As estruturas temporárias foram removidas; os registros originais permaneceram inalterados.
