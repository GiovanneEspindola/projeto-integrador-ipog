// P12 — Produtos comprados juntos
// Pergunta: Quais produtos aparecem juntos no mesmo pedido?
// Resultado: Pares de produtos que aparecem no mesmo pedido, quantos pedidos contêm cada par e o suporte (%).
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "orders",
  pipeline: [
    {
      $match: {
        order_date: {$gte: ISODate("1996-07-01T00:00:00Z"), $lt: ISODate("1998-06-01T00:00:00Z")}
      }
    },
    {
      $facet: {
        total: [{$count: "n"}],
        pares: [
          {$project: {_id: 0, ids: "$items.product._id"}},
          {$set: {outros: "$ids"}},
          {$unwind: "$ids"},
          {$unwind: "$outros"},
          {$match: {$expr: {$lt: ["$ids", "$outros"]}}},
          {$group: {_id: {a: "$ids", b: "$outros"}, pedidos: {$sum: 1}}}
        ]
      }
    },
    {$set: {denominador: {$ifNull: [{$first: "$total.n"}, 0]}}},
    {$unwind: "$pares"},
    {
      $project: {
        _id: 0,
        produto_a: "$pares._id.a",
        produto_b: "$pares._id.b",
        pedidos: "$pares.pedidos",
        denominador: 1,
        suporte: {
          $cond: [
            {$eq: ["$denominador", 0]},
            null,
            {
              $divide: [{$multiply: ["$pares.pedidos", Decimal128("100")]}, "$denominador"]
            }
          ]
        }
      }
    },
    {$sort: {pedidos: -1, produto_a: 1, produto_b: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
