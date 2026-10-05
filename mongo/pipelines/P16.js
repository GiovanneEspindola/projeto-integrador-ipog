// P16 — Distribuição trimestral por ano e categoria
// Pergunta: Como o valor se distribui por ano, trimestre e categoria?
// Resultado: Valor por ano e trimestre, total e por categoria, marcando trimestres com cobertura parcial dos dados.
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
        ano: {$year: "$order_date"},
        trimestre: {$toInt: {$ceil: {$divide: [{$month: "$order_date"}, 3]}}},
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
      $facet: {
        total: [
          {$group: {_id: {ano: "$ano", trimestre: "$trimestre"}, valor: {$sum: "$valor"}}},
          {
            $project: {
              _id: 0,
              ano: "$_id.ano",
              trimestre: "$_id.trimestre",
              category_id: {$literal: null},
              valor: 1,
              nivel: {$literal: "total"}
            }
          }
        ],
        categoria: [
          {
            $group: {
              _id: {
                ano: "$ano",
                trimestre: "$trimestre",
                category_id: "$items.product.category._id"
              },
              valor: {$sum: "$valor"}
            }
          },
          {
            $project: {
              _id: 0,
              ano: "$_id.ano",
              trimestre: "$_id.trimestre",
              category_id: "$_id.category_id",
              valor: 1,
              nivel: {$literal: "categoria"}
            }
          }
        ]
      }
    },
    {$project: {linhas: {$concatArrays: ["$total", "$categoria"]}}},
    {$unwind: "$linhas"},
    {$replaceWith: "$linhas"},
    {
      $set: {
        inicio_trimestre: {
          $dateFromParts: {
            year: "$ano",
            month: {$add: [{$multiply: [{$subtract: ["$trimestre", 1]}, 3]}, 1]}
          }
        }
      }
    },
    {
      $set: {
        parcial: {
          $or: [
            {$lt: ["$inicio_trimestre", ISODate("1996-07-04T00:00:00Z")]},
            {
              $gt: [
                {$dateAdd: {startDate: "$inicio_trimestre", unit: "month", amount: 3}},
                ISODate("1998-05-07T00:00:00Z")
              ]
            }
          ]
        }
      }
    },
    {$unset: "inicio_trimestre"},
    {$sort: {ano: 1, trimestre: 1, category_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
