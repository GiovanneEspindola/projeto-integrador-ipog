# 9. Índices no MongoDB

Além do índice automático em _id, foram criados três índices, cada um ligado a um acesso concreto:

| Índice | Campos | Acesso atendido |
|---|---|---|
| cliente_data | customer_id, order_date | Pedidos de um cliente num período, em ordem de data |
| produto_no_pedido | items.product._id | Pedidos que contêm um produto |
| categoria_produto | category._id | Produtos de uma categoria |

No índice composto, o cliente vem primeiro porque é filtrado por igualdade; a data vem depois e atende ao intervalo e à ordenação. O índice em items.product._id é multikey: ele indexa cada produto do array de itens.

```javascript
db.orders.find({
  customer_id: "VINET",
  order_date: {
    $gte: ISODate("1996-01-01T00:00:00Z"),
    $lt: ISODate("1997-01-01T00:00:00Z")
  }
}).sort({ order_date: 1 }).explain("executionStats");
```

| Medida | Resultado |
|---|---|
| Plano | FETCH → IXSCAN |
| Índice usado | cliente_data |
| Documentos examinados / retornados | 3 / 3 |

Sem índice, o MongoDB leria os 830 pedidos para devolver três. Com ele, lê exatamente os três. O plano de P03 (capítulo 13) mostrou também o uso de produto_no_pedido. Índices custam espaço e tornam as escritas mais lentas, por isso não foram criados para todos os campos. Como o capítulo 16 mostra, faltaram dois que fariam diferença.
