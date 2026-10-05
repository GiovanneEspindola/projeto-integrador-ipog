// P09 — Variação mensal do valor
// Pergunta: Quanto o valor mudou em relação ao mês anterior?
// Resultado: Valor de cada mês comparado ao mês anterior: diferença absoluta e variação percentual.
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
        output: {anterior: {$shift: {output: "$valor", by: -1, default: null}}}
      }
    },
    {$set: {variacao: {$subtract: ["$valor", "$anterior"]}}},
    {
      $project: {
        _id: 0,
        mes: {$dateToString: {date: "$mes", format: "%Y-%m-%d"}},
        valor: 1,
        anterior: 1,
        variacao: 1,
        percentual: {
          $cond: [
            {$eq: ["$anterior", 0]},
            null,
            {$divide: [{$multiply: ["$variacao", Decimal128("100")]}, "$anterior"]}
          ]
        }
      }
    },
    {$sort: {mes: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
