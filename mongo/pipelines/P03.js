// P03 — Produtos sem vendas no período
// Pergunta: Quais produtos não foram vendidos no período?
// Resultado: Produtos do catálogo sem nenhum item vendido na janela; lista vazia significa que todos venderam.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "products",
  pipeline: [
    {
      $lookup: {
        from: "orders",
        localField: "_id",
        foreignField: "items.product._id",
        pipeline: [
          {
            $match: {
              order_date: {
                $gte: ISODate("1996-07-01T00:00:00Z"),
                $lt: ISODate("1998-06-01T00:00:00Z")
              }
            }
          },
          {$limit: 1},
          {$project: {_id: 0, encontrado: {$literal: true}}}
        ],
        as: "vendas"
      }
    },
    {$match: {vendas: {$size: 0}}},
    {
      $project: {
        _id: 0,
        product_id: "$_id",
        produto: "$product_name",
        categoria: "$category.name",
        fornecedor: "$supplier.name"
      }
    },
    {$sort: {product_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
