# 11. Regras comuns às análises

As 16 perguntas foram respondidas duas vezes: uma consulta SQL (QNN.sql) e um pipeline MongoDB (PNN.js) para cada uma. Para que os dois lados pudessem ser comparados número a número, as regras abaixo foram fixadas antes de escrever qualquer código.

| Regra | Definição |
|---|---|
| Período | De 01/07/1996 (incluído) a 01/06/1998 (excluído), que cobre todos os pedidos |
| Valor | preço praticado × quantidade × (1 − desconto), sem frete, com decimais exatos |
| Arredondamento | Só na apresentação, com duas casas; nenhuma soma usa valores arredondados |
| Ticket | Valor dos pedidos ÷ número de pedidos; os itens são somados por pedido antes |
| Referência de recência | 06/05/1998, último pedido; inativo é quem não compra desde antes de 06/11/1997 |
| Meses vazios | As séries mensais têm os 23 meses, com zero onde não houver pedidos |
| Cadastros sem movimento | Clientes, funcionários e transportadoras sem pedidos aparecem com zero |
| Desempate | Sempre pelo identificador, para que a ordem seja a mesma nos dois bancos |

Duas regras merecem destaque. Primeiro, a **curva ABC** classifica pelo valor acumulado antes de cada cliente: é classe A quem entra enquanto o acumulado está abaixo de 80% do total, B abaixo de 95% e C o restante. Segundo, o **RFM** usa faixas fixas e didáticas: recência até 30 dias = 3, até 90 = 2, acima = 1; frequência de pelo menos 10 pedidos = 3, pelo menos 5 = 2; valor de pelo menos 10.000 = 3, pelo menos 5.000 = 2. Quem nunca comprou recebe zero.

## 11.1 Como os resultados foram conferidos

Cada par foi comparado linha a linha e campo a campo, na ordem em que os bancos devolvem os dados. Somas de dinheiro precisam ser exatamente iguais; médias e percentuais admitem diferença de até 0,000000000001, por causa das dízimas.

SQL e MongoDB poderiam errar a mesma regra e ainda concordar entre si. Por isso, houve mais duas verificações:

- **Um terceiro cálculo**, em Python puro, a partir das linhas brutas de nw, sem SQL analítico. Os 16 resultados bateram.
- **Testes com quatro pedidos inventados**, numa base isolada, cujo resultado foi calculado à mão: mês sem vendas, compra exatamente no dia do corte de inatividade, item de 0,005, pedido sem data de envio e empate no ranking. Ao todo, 38 verificações, todas aprovadas.
