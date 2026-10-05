# 10. Conferência da migração

## 10.1 Equivalência dos registros

A conferência foi realizada em 10/09/2026, mediante a leitura dos documentos gravados no MongoDB e a reconstrução das linhas das 11 tabelas de nw. Os itens foram separados dos pedidos, os campos dos endereços foram desagrupados e os vínculos entre funcionários e territórios foram reconstituídos. Esse procedimento foi desenvolvido separadamente da transformação utilizada na carga.

As linhas reconstruídas foram comparadas com a origem por **EXCEPT ALL nos dois sentidos**. A comparação abrangeu os campos e as ocorrências de cada linha, permitindo identificar registros ausentes, extras, duplicados ou com valores alterados. Os decimais foram comparados sem arredondamento prévio, e datas com horário diferente da convenção de meia-noite UTC foram recusadas antes da comparação.

| Tabela reconstruída | Origem | MongoDB | Diferenças |
|---|---|---|---|
| regions | 4 | 4 | 0 |
| territories | 53 | 53 | 0 |
| categories | 8 | 8 | 0 |
| shippers | 6 | 6 | 0 |
| suppliers | 29 | 29 | 0 |
| customers | 91 | 91 | 0 |
| employees | 9 | 9 | 0 |
| employee_territories | 49 | 49 | 0 |
| products | 77 | 77 | 0 |
| orders | 830 | 830 | 0 |
| order_items | 2.155 | 2.155 | 0 |
| Total | 3.311 | 3.311 | 0 |

As **3.311 linhas** foram reconstruídas sem divergências. Também foram conferidos os tipos BSON, as referências entre coleções, os nomes e categorias copiados para os itens, os territórios incorporados e a coerência das datas. A comparação foi repetida após a segunda carga, mantendo zero diferenças.

## 10.2 Precisão dos valores

A soma dos itens foi calculada separadamente nos dois bancos pela expressão **preço praticado × quantidade × (1 − desconto)**, sem inclusão do frete. PostgreSQL e MongoDB retornaram o mesmo valor decimal exato: **1265793.03950**. Com arredondamento apenas após a soma, o valor apresentado é **1.265.793,04**.

A conferência não utilizou as views que arredondam cada item. A comparação exata também evita depender das diferenças entre round(numeric) do PostgreSQL e $round do MongoDB em casos de empate [4, 11].

Como teste adicional, uma cópia dos dados de retorno recebeu o preço 14.004 em lugar de 14.00. A comparação identificou duas diferenças: a ausência da linha original e a presença da linha alterada. O teste confirmou que uma diferença inferior a um centavo não foi ocultada por arredondamento. Nenhum registro dos bancos foi alterado nesse teste.
