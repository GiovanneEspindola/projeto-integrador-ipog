# 9. Estratégia de indexação

## 9.1 Índices associados a consultas

Além do índice único automático em _id de cada coleção, foram criados três índices adicionais. Eles atendem a formas concretas de acesso previstas para o modelo.

| Índice | Campos | Consulta atendida |
|---|---|---|
| cliente_data | customer_id: 1, order_date: 1 | Pedidos de um cliente em determinado período, ordenados por data. |
| produto_no_pedido | items.product._id: 1 | Pedidos que contêm determinado produto. |
| categoria_produto | category._id: 1 | Produtos cadastrados em uma categoria. |

No índice composto, o cliente é usado por igualdade e a data permite o intervalo e a ordenação. O índice em items.product._id é **multikey**: o MongoDB cria entradas para valores encontrados no array de itens [10]. Não foi usado índice único nesse campo, porque o mesmo produto pode aparecer em vários pedidos.

```javascript
db.orders.createIndex(
  { customer_id: 1, order_date: 1 },
  { name: "cliente_data" }
);
```

## 9.2 Evidência do plano de execução

A consulta abaixo foi executada com explain, sem forçar índice com hint:

```javascript
db.orders.find({
  customer_id: "VINET",
  order_date: {
    $gte: ISODate("1996-01-01T00:00:00Z"),
    $lt: ISODate("1997-01-01T00:00:00Z")
  }
}).sort({ order_date: 1 }).explain("executionStats");
```

| Medida observada | Resultado |
|---|---|
| Plano vencedor | FETCH → IXSCAN |
| Índice utilizado | cliente_data |
| Documentos retornados | 3 |
| Documentos examinados | 3 |
| Chaves examinadas | 3 |

**IXSCAN** indica leitura pelo índice; **FETCH** indica a busca dos documentos correspondentes. A consulta retorna três pedidos de VINET em 1996. Esse resultado demonstra uso do índice nessa consulta, sem justificar uma conclusão geral sobre superioridade do MongoDB.

Índices consomem espaço e precisam ser mantidos durante as escritas. Por isso, não foram criados índices para todos os campos. A observação realizada sustenta o uso do índice composto para o filtro e a ordenação examinados. Os outros dois índices foram definidos pelos acessos previstos, mas seus planos de execução não foram avaliados nesta análise. A comparação de desempenho entre bancos permanece em aberto.
