// Executar somente na cópia isolada definida pelo benchmark.
var consulta = EJSON.parse("{\"collection\": \"orders\", \"pipeline\": [{\"$match\": {\"customer_id\": \"VINET\", \"order_date\": {\"$gte\": {\"$date\": \"1996-01-01T00:00:00Z\"}, \"$lt\": {\"$date\": \"1997-01-01T00:00:00Z\"}}}}, {\"$sort\": {\"order_date\": 1, \"_id\": 1}}, {\"$project\": {\"_id\": 0, \"order_id\": \"$_id\", \"order_date\": {\"$dateToString\": {\"date\": \"$order_date\", \"format\": \"%Y-%m-%d\"}}}}]}");
print(EJSON.stringify(db.getCollection(consulta.collection)
  .aggregate(consulta.pipeline).toArray(), null, 2));
