// P06 — Clientes inativos e sem compras
// Pergunta: Quais clientes estão sem compra há mais de seis meses?
// Resultado: Clientes sem compra desde antes de 06/11/1997 (inativos) e clientes que nunca compraram.
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
    {$match: {$or: [{ultima: null}, {ultima: {$lt: ISODate("1997-11-06T00:00:00Z")}}]}},
    {
      $project: {
        _id: 0,
        customer_id: "$_id",
        cliente: "$company_name",
        ultima: {
          $dateToString: {date: "$ultima", format: "%Y-%m-%d", timezone: "UTC", onNull: null}
        },
        recencia: {
          $dateDiff: {startDate: "$ultima", endDate: ISODate("1998-05-06T00:00:00Z"), unit: "day"}
        },
        situacao: {$cond: [{$eq: ["$ultima", null]}, "sem compras", "inativo"]}
      }
    },
    {$sort: {customer_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
