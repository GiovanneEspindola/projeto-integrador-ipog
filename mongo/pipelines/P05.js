// P05 — Estoque crítico e cobertura por categoria
// Pergunta: Quais categorias têm produtos abaixo do ponto de reposição?
// Resultado: Categorias com produtos abaixo do ponto de reposição, déficit somado e quantos nem com o encomendado se cobrem.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "products",
  pipeline: [
    {$match: {$expr: {$lt: ["$units_in_stock", "$reorder_level"]}}},
    {
      $set: {
        deficit: {$subtract: ["$reorder_level", "$units_in_stock"]},
        insuficiente: {
          $cond: [
            {$lt: [{$add: ["$units_in_stock", "$units_on_order"]}, "$reorder_level"]},
            1,
            0
          ]
        }
      }
    },
    {$sort: {_id: 1}},
    {
      $group: {
        _id: "$category._id",
        categoria: {$first: "$category.name"},
        produtos: {$sum: 1},
        deficit: {$sum: "$deficit"},
        reposicao_insuficiente: {$sum: "$insuficiente"},
        produtos_ids: {$push: "$_id"}
      }
    },
    {
      $project: {
        _id: 0,
        category_id: "$_id",
        categoria: 1,
        produtos: 1,
        deficit: 1,
        reposicao_insuficiente: 1,
        produtos_ids: 1
      }
    },
    {$sort: {category_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
