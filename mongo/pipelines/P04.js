// P04 — Indicadores por funcionário
// Pergunta: Como se distribuem os pedidos entre os funcionários?
// Resultado: Uma linha por funcionário, inclusive sem pedidos: pedidos, valor, valor médio por pedido e fatia do total.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "employees",
  pipeline: [
    {
      $lookup: {
        from: "orders",
        localField: "_id",
        foreignField: "employee_id",
        pipeline: [
          {
            $match: {
              order_date: {
                $gte: ISODate("1996-07-01T00:00:00Z"),
                $lt: ISODate("1998-06-01T00:00:00Z")
              }
            }
          },
          {
            $group: {
              _id: null,
              pedidos: {$sum: 1},
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
        as: "vendas"
      }
    },
    {
      $set: {
        pedidos: {$ifNull: [{$first: "$vendas.pedidos"}, 0]},
        valor: {$ifNull: [{$first: "$vendas.valor"}, Decimal128("0")]}
      }
    },
    {
      $setWindowFields: {output: {total: {$sum: "$valor", window: {documents: ["unbounded", "unbounded"]}}}}
    },
    {
      $project: {
        _id: 0,
        employee_id: "$_id",
        funcionario: {$concat: ["$first_name", " ", "$last_name"]},
        pedidos: 1,
        valor: 1,
        ticket: {$cond: [{$eq: ["$pedidos", 0]}, null, {$divide: ["$valor", "$pedidos"]}]},
        participacao: {
          $cond: [
            {$eq: ["$total", 0]},
            null,
            {$divide: [{$multiply: ["$valor", Decimal128("100")]}, "$total"]}
          ]
        }
      }
    },
    {$sort: {employee_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
