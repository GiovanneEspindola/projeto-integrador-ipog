// P11 — RFM descritivo dos clientes
// Pergunta: Qual é o perfil de recência, frequência e valor de cada cliente?
// Resultado: Recência (dias), frequência (pedidos) e valor de cada cliente, com escores 0 a 3 em faixas fixas.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "customers",
  pipeline: [
    {
      $lookup: {
        from: "orders",
        localField: "_id",
        foreignField: "customer_id",
        pipeline: [
          {$match: {order_date: {$lte: ISODate("1998-05-06T00:00:00Z")}}},
          {
            $group: {
              _id: null,
              ultima: {$max: "$order_date"},
              frequencia: {$sum: 1},
              valor: {
                $sum: {
                  $sum: {
                    $map: {
                      input: "$items",
                      as: "i",
                      in: {
                        $multiply: [
                          "$$i.unit_price",
                          "$$i.quantity",
                          {$subtract: [Decimal128("1"), "$$i.discount"]}
                        ]
                      }
                    }
                  }
                }
              }
            }
          }
        ],
        as: "compras"
      }
    },
    {
      $set: {
        ultima: {$ifNull: [{$first: "$compras.ultima"}, null]},
        frequencia: {$ifNull: [{$first: "$compras.frequencia"}, 0]},
        valor: {$ifNull: [{$first: "$compras.valor"}, Decimal128("0")]}
      }
    },
    {
      $set: {
        recencia: {
          $dateDiff: {startDate: "$ultima", endDate: ISODate("1998-05-06T00:00:00Z"), unit: "day"}
        }
      }
    },
    {
      $project: {
        _id: 0,
        customer_id: "$_id",
        recencia: 1,
        frequencia: 1,
        valor: 1,
        r: {
          $cond: [
            {$eq: ["$frequencia", 0]},
            0,
            {
              $cond: [{$lte: ["$recencia", 30]}, 3, {$cond: [{$lte: ["$recencia", 90]}, 2, 1]}]
            }
          ]
        },
        f: {
          $cond: [
            {$eq: ["$frequencia", 0]},
            0,
            {
              $cond: [
                {$gte: ["$frequencia", 10]},
                3,
                {$cond: [{$gte: ["$frequencia", 5]}, 2, 1]}
              ]
            }
          ]
        },
        m: {
          $cond: [
            {$eq: ["$frequencia", 0]},
            0,
            {
              $cond: [
                {$gte: ["$valor", Decimal128("10000")]},
                3,
                {$cond: [{$gte: ["$valor", Decimal128("5000")]}, 2, 1]}
              ]
            }
          ]
        }
      }
    },
    {$sort: {customer_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
