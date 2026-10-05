// P14 — Descontos sobre o valor dos pedidos
// Pergunta: Quanto os descontos reduzem o valor bruto dos itens?
// Resultado: Por categoria: valor bruto, desconto concedido, valor após descontos e taxa ponderada de desconto.
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
      $set: {
        bruto: {$multiply: ["$items.unit_price", "$items.quantity"]},
        desconto: {$multiply: ["$items.unit_price", "$items.quantity", "$items.discount"]},
        valor: {
          $multiply: [
            "$items.unit_price",
            "$items.quantity",
            {$subtract: [Decimal128("1"), "$items.discount"]}
          ]
        }
      }
    },
    {
      $group: {
        _id: "$items.product.category._id",
        bruto: {$sum: "$bruto"},
        desconto: {$sum: "$desconto"},
        valor: {$sum: "$valor"}
      }
    },
    {
      $project: {
        _id: 0,
        category_id: "$_id",
        bruto: 1,
        desconto: 1,
        valor: 1,
        percentual_desconto: {
          $cond: [
            {$eq: ["$bruto", 0]},
            null,
            {$divide: [{$multiply: ["$desconto", Decimal128("100")]}, "$bruto"]}
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
