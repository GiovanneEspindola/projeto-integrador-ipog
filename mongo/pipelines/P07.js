// P07 — Top cinco produtos por categoria
// Pergunta: Quais são os cinco produtos de maior valor em cada categoria?
// Resultado: Até cinco produtos de maior valor em cada categoria, com posição 1 a 5 e desempate pelo menor ID.
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
        _id: {c: "$items.product.category._id", p: "$items.product._id"},
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
    {$project: {_id: 0, category_id: "$_id.c", product_id: "$_id.p", valor: 1}},
    {
      $setWindowFields: {
        partitionBy: "$category_id",
        sortBy: {valor: -1, product_id: 1},
        output: {posicao: {$sum: 1, window: {documents: ["unbounded", "current"]}}}
      }
    },
    {$match: {posicao: {$lte: 5}}},
    {$sort: {category_id: 1, posicao: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
