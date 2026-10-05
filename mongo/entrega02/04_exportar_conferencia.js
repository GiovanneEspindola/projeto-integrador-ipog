// Reconstrói linhas relacionais a partir do banco realmente gravado.
// Não lê o arquivo de carga nem reaproveita sua transformação SQL.
var b = db.getSiblingDB('northwind');
var linhas = {};
var ler = nome => b.getCollection(nome).find({}).toArray();
var renomear = (doc, chave) => {var {_id,...resto}=doc; return {[chave]:_id,...resto};};
var abrirEndereco = endereco => ({address:endereco.street,city:endereco.city,
  region:endereco.region,postal_code:endereco.postal_code,country:endereco.country});
for (var [colecao,chave] of Object.entries({regions:'region_id',territories:'territory_id',categories:'category_id',shippers:'shipper_id'})) {
  linhas[colecao]=ler(colecao).map(d=>renomear(d,chave));
}
for (var [colecao,chave] of Object.entries({customers:'customer_id',suppliers:'supplier_id'})) {
  linhas[colecao]=ler(colecao).map(d=>{var {address,...r}=renomear(d,chave);return {...r,...abrirEndereco(address)};});
}
linhas.products=ler('products').map(d=>{var {category,supplier,...r}=renomear(d,'product_id');return {...r,category_id:category._id,supplier_id:supplier._id};});
linhas.employee_territories=[];
linhas.employees=ler('employees').map(d=>{
  var {address,territories,...r}=renomear(d,'employee_id');
  for(var t of territories) linhas.employee_territories.push({employee_id:d._id,territory_id:t.territory_id});
  return {...r,...abrirEndereco(address)};
});
linhas.order_items=[];
linhas.orders=ler('orders').map(d=>{
  var {items,shipping,...r}=renomear(d,'order_id');
  for(var i of items) linhas.order_items.push({order_id:d._id,product_id:i.product._id,
    unit_price:i.unit_price,quantity:i.quantity,discount:i.discount});
  return {...r,ship_name:shipping.name,ship_address:shipping.street,ship_city:shipping.city,
    ship_region:shipping.region,ship_postal_code:shipping.postal_code,ship_country:shipping.country};
});
// Dinheiro vai como texto decimal exato; a conferência SQL o reconverte a
// numeric no PostgreSQL. Datas são dias UTC, sem deslocamento para o fuso local.
function normalizar(x) {
  if (x===null) return null;
  if (x instanceof Date) {
    if (!x.toISOString().endsWith('T00:00:00.000Z')) throw new Error('Data fora da convenção UTC: '+x.toISOString());
    return x.toISOString().slice(0,10);
  }
  if (x?._bsontype==='Decimal128') return x.toString();
  if (x?._bsontype==='Int32') return x.valueOf();
  if (Array.isArray(x)) return x.map(normalizar);
  if (typeof x==='object') return Object.fromEntries(Object.entries(x).map(([k,v])=>[k,normalizar(v)]));
  return x;
}
print(JSON.stringify(normalizar(linhas)));
