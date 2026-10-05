// P01 — Valor e participação por categoria
// Pergunta: Quais categorias concentram o valor dos pedidos?
// Resultado: Uma linha por categoria com vendas: unidades, valor após descontos e fatia (%) do valor total.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "orders",
  pipeline: [
    {
      $match: {
        order_date: {$gte: ISODate("1996-07-01T00:00:00Z"), $lt: ISODate("1998-06-01T00:00:00Z")}
      }
    },
    {$unwind: "$items"},
    {
      $group: {
        _id: "$items.product.category._id",
        categoria: {$first: "$items.product.category.name"},
        unidades: {$sum: "$items.quantity"},
        valor: {
          $sum: {
            $multiply: [
              "$items.unit_price",
              "$items.quantity",
              {$subtract: [Decimal128("1"), "$items.discount"]}
            ]
          }
        }
      }
    },
    {
      $setWindowFields: {output: {total: {$sum: "$valor", window: {documents: ["unbounded", "unbounded"]}}}}
    },
    {
      $project: {
        _id: 0,
        category_id: "$_id",
        categoria: 1,
        unidades: 1,
        valor: 1,
        participacao: {
          $cond: [
            {$eq: ["$total", 0]},
            null,
            {$divide: [{$multiply: ["$valor", Decimal128("100")]}, "$total"]}
          ]
        }
      }
    },
    {$sort: {category_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
