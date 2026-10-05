// P15 — Vendas próprias e da equipe
// Pergunta: Quanto foi registrado por cada funcionário e sua equipe?
// Resultado: Por funcionário: tamanho da equipe (ele e subordinados), valor próprio e valor da equipe; equipes se sobrepõem.
// Datas UTC; Decimal128; saída ordenada equivalente ao SQL.
var consulta = {
  collection: "employees",
  pipeline: [
    {
      $graphLookup: {
        from: "employees",
        startWith: "$_id",
        connectFromField: "_id",
        connectToField: "reports_to",
        as: "subordinados"
      }
    },
    {$set: {membro_ids: {$setUnion: [["$_id"], "$subordinados._id"]}}},
    {
      $lookup: {
        from: "orders",
        localField: "membro_ids",
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
              _id: "$employee_id",
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
      $project: {
        _id: 0,
        gestor_id: "$_id",
        membros: {$size: "$membro_ids"},
        valor_proprio: {
          $sum: {
            $map: {
              input: {$filter: {input: "$vendas", as: "v", cond: {$eq: ["$$v._id", "$_id"]}}},
              as: "v",
              in: "$$v.valor"
            }
          }
        },
        pedidos_equipe: {$sum: "$vendas.pedidos"},
        valor_equipe: {$sum: "$vendas.valor"}
      }
    },
    {$sort: {gestor_id: 1}}
  ]
};
if (typeof ANALYTICS_EXPORT === 'undefined') {
  print(EJSON.stringify(db.getSiblingDB('northwind')
    .getCollection(consulta.collection).aggregate(consulta.pipeline).toArray(), null, 2));
}
