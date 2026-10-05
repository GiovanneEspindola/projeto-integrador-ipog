# 10. Conferência da migração

Contar documentos não basta: duas tabelas com dez linhas podem ter preços diferentes. A prova adotada foi o caminho inverso. Os documentos gravados no MongoDB foram lidos de volta, desmontados em linhas (itens separados dos pedidos, endereços desagrupados, territórios reconstituídos) e comparados com as 11 tabelas de nw, campo a campo, nos dois sentidos, com EXCEPT ALL. Esse procedimento foi escrito separadamente da carga, para não repetir um eventual erro dela.

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

**As 3.311 linhas voltaram sem nenhuma diferença.** A soma dos itens também foi calculada nos dois bancos, com decimais exatos, e deu o mesmo valor: **1265793.03950**, apresentado como 1.265.793,04.

Para ter certeza de que a comparação não escondia diferenças pequenas, uma cópia dos dados recebeu o preço 14.004 no lugar de 14.00. A comparação acusou a mudança, ou seja, detecta diferenças menores que um centavo. A conferência foi repetida nas Entregas 3 e 4, sempre com zero diferenças.
