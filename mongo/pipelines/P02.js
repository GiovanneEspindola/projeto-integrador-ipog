// P02 — Pedidos e ticket médio mensal
// Pergunta: Como variam o número de pedidos e o ticket médio mensal?
// Resultado: Uma linha por mês, inclusive sem pedidos: quantidade de pedidos, valor e valor médio por pedido.
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
      $set: {
        valor: {
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
    },
    {
      $facet: {
        dados: [
          {
            $group: {
              _id: {$dateTrunc: {date: "$order_date", unit: "month", timezone: "UTC"}},
              pedidos: {$sum: 1},
              valor: {$sum: "$valor"}
            }
          }
        ]
      }
    },
    {
      $project: {
        linhas: {
          $map: {
            input: {
              $range: [
                0,
                {
                  $dateDiff: {
                    startDate: ISODate("1996-07-01T00:00:00Z"),
                    endDate: ISODate("1998-06-01T00:00:00Z"),
                    unit: "month"
                  }
                }
              ]
            },
            as: "k",
            in: {
              $let: {
                vars: {
                  m: {
                    $dateAdd: {
                      startDate: ISODate("1996-07-01T00:00:00Z"),
                      unit: "month",
                      amount: "$$k"
                    }
                  }
                },
                in: {
                  $let: {
                    vars: {
                      r: {
                        $arrayElemAt: [
                          {
                            $filter: {input: "$dados", as: "d", cond: {$eq: ["$$d._id", "$$m"]}}
                          },
                          0
                        ]
                      }
                    },
                    in: {
                      mes: "$$m",
                      pedidos: {$ifNull: ["$$r.pedidos", 0]},
                      valor: {$ifNull: ["$$r.valor", Decimal128("0")]}
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    {$unwind: "$linhas"},
    {$replaceWith: "$linhas"},
    {
      $project: {
        _id: 0,
        mes: {$dateToString: {date: "$mes", format: "%Y-%m-%d", timezone: "UTC"}},
        pedidos: 1,
        valor: 1,
        ticket: {$cond: [{$eq: ["$pedidos", 0]}, null, {$divide: ["$valor", "$pedidos"]}]}
      }
    },
    {$sort: {mes: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
