// P13 — Intervalo até envio por transportadora
// Pergunta: Qual é o intervalo até o envio registrado por transportadora?
// Resultado: Por transportadora: pedidos, datas de envio registradas e ausentes, média de dias até o envio e envios após a data requerida.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "shippers",
  pipeline: [
    {
      $lookup: {
        from: "orders",
        localField: "_id",
        foreignField: "shipper_id",
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
              com_envio: {$sum: {$cond: [{$ne: ["$shipped_date", null]}, 1, 0]}},
              soma_dias: {
                $sum: {
                  $dateDiff: {startDate: "$order_date", endDate: "$shipped_date", unit: "day"}
                }
              },
              apos_requerida: {$sum: {$cond: [{$gt: ["$shipped_date", "$required_date"]}, 1, 0]}}
            }
          }
        ],
        as: "res"
      }
    },
    {
      $set: {
        pedidos: {$ifNull: [{$first: "$res.pedidos"}, 0]},
        com_envio: {$ifNull: [{$first: "$res.com_envio"}, 0]},
        soma_dias: {$ifNull: [{$first: "$res.soma_dias"}, 0]},
        apos_requerida: {$ifNull: [{$first: "$res.apos_requerida"}, 0]}
      }
    },
    {
      $project: {
        _id: 0,
        shipper_id: "$_id",
        transportadora: "$company_name",
        pedidos: 1,
        com_envio: 1,
        sem_data: {$subtract: ["$pedidos", "$com_envio"]},
        soma_dias: 1,
        apos_requerida: 1,
        media_dias: {
          $cond: [
            {$eq: ["$com_envio", 0]},
            null,
            {$divide: [{$toDecimal: "$soma_dias"}, "$com_envio"]}
          ]
        }
      }
    },
    {$sort: {shipper_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
