// Executar somente na cópia isolada definida pelo benchmark.
var consulta = EJSON.parse("{\"collection\": \"orders\", \"pipeline\": [{\"$set\": {\"mes\": {\"$dateToString\": {\"date\": \"$order_date\", \"format\": \"%Y-%m\"}}}}, {\"$match\": {\"mes\": \"1997-01\"}}, {\"$group\": {\"_id\": null, \"pedidos\": {\"$sum\": 1}, \"valor\": {\"$sum\": {\"$sum\": {\"$map\": {\"input\": \"$items\", \"as\": \"i\", \"in\": {\"$multiply\": [\"$$i.unit_price\", \"$$i.quantity\", {\"$subtract\": [{\"$toDecimal\": 1}, \"$$i.discount\"]}]}}}}}}}, {\"$project\": {\"_id\": 0, \"mes\": {\"$literal\": \"1997-01-01\"}, \"pedidos\": 1, \"valor\": 1}}]}");
print(EJSON.stringify(db.getCollection(consulta.collection)
  .aggregate(consulta.pipeline).toArray(), null, 2));
