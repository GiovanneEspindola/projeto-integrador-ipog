// MapReduce é requisito didático legado. Somente quantidades inteiras.
var b = db.getSiblingDB('northwind');
var resultado = b.runCommand({
  mapReduce: 'orders',
  map: function () {
    this.items.forEach(function (i) { emit(i.product._id, i.quantity); });
  },
  reduce: function (produto, quantidades) { return Array.sum(quantidades); },
  out: { inline: 1 }
});
if (resultado.ok !== 1) throw new Error(EJSON.stringify(resultado));
var pipeline = [
  {$unwind: '$items'},
  {$group: {_id: '$items.product._id', value: {$sum: '$items.quantity'}}},
  {$sort: {_id: 1}}
];
var moderno = b.orders.aggregate(pipeline).toArray();
var legado = resultado.results.sort((a,b) => a._id-b._id);
require('assert').deepStrictEqual(
  legado.map(x=>[Number(x._id),Number(x.value)]),
  moderno.map(x=>[Number(x._id),Number(x.value)])
);
print(EJSON.stringify({equivalente:true,produtos:moderno.length,
  unidades:moderno.reduce((s,x)=>s+Number(x.value),0),resultados:legado},null,2));
