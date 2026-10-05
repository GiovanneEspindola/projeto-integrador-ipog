// P10 — Curva ABC de clientes
// Pergunta: Como os clientes se distribuem pela curva ABC de valor?
// Resultado: Todos os clientes ordenados por valor, com acumulado e classe A/B/C pela concentração do valor.
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
        as: "compras"
      }
    },
    {
      $set: {
        pedidos: {$ifNull: [{$first: "$compras.pedidos"}, 0]},
        valor: {$ifNull: [{$first: "$compras.valor"}, Decimal128("0")]}
      }
    },
    {
      $setWindowFields: {
        sortBy: {valor: -1, _id: 1},
        output: {
          acumulado: {$sum: "$valor", window: {documents: ["unbounded", "current"]}},
          total: {$sum: "$valor", window: {documents: ["unbounded", "unbounded"]}}
        }
      }
    },
    {
      $project: {
        _id: 0,
        customer_id: "$_id",
        cliente: "$company_name",
        pedidos: 1,
        valor: 1,
        acumulado: 1,
        classe: {
          $switch: {
            branches: [
              {case: {$eq: ["$pedidos", 0]}, then: "sem compras"},
              {
                case: {
                  $lt: [
                    {$subtract: ["$acumulado", "$valor"]},
                    {$multiply: ["$total", Decimal128("0.80")]}
                  ]
                },
                then: "A"
              },
              {
                case: {
                  $lt: [
                    {$subtract: ["$acumulado", "$valor"]},
                    {$multiply: ["$total", Decimal128("0.95")]}
                  ]
                },
                then: "B"
              }
            ],
            default: "C"
          }
        }
      }
    },
    {$sort: {valor: -1, customer_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
