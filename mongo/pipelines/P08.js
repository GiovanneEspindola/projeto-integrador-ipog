// P08 — Valor mensal acumulado
// Pergunta: Qual é o valor acumulado ao longo dos meses?
// Resultado: Valor de cada mês e o valor acumulado desde julho de 1996; o último acumulado é o total do período.
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
      $setWindowFields: {
        sortBy: {mes: 1},
        output: {acumulado: {$sum: "$valor", window: {documents: ["unbounded", "current"]}}}
      }
    },
    {
      $project: {
        _id: 0,
        mes: {$dateToString: {date: "$mes", format: "%Y-%m-%d"}},
        valor: 1,
        acumulado: 1
      }
    },
    {$sort: {mes: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
