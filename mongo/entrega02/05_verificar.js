// Verificações complementares sobre BSON, dados duplicados de cadastros e índices.
load('/mongo/entrega02/01_modelo.js');
var b=db.getSiblingDB('northwind');
for(var [nome,schema] of Object.entries(modelos)) {
  assert.eq(b.getCollection(nome).countDocuments({$nor:[{$jsonSchema:schema}]}),0,'Estrutura inválida: '+nome);
}
var porId=nome=>new Map(b.getCollection(nome).find({}).toArray().map(d=>[String(d._id),d]));
var products=porId('products'), categories=porId('categories'), suppliers=porId('suppliers');
var territories=porId('territories'), regions=porId('regions'), customers=porId('customers');
var employees=porId('employees'), shippers=porId('shippers');
for(var p of products.values()) {
  assert.eq(p.category.name,categories.get(String(p.category._id))?.category_name,'Categoria copiada incorretamente');
  assert.eq(p.supplier.name,suppliers.get(String(p.supplier._id))?.company_name,'Fornecedor copiado incorretamente');
}
for(var t of territories.values()) assert(regions.has(String(t.region_id)),'Região inexistente');
for(var e of employees.values()) {
  assert(e.reports_to===null || employees.has(String(e.reports_to)),'Chefia inexistente');
  assert(e.hire_date>e.birth_date,'Datas do funcionário inválidas');
  assert.eq(new Set(e.territories.map(t=>t.territory_id)).size,e.territories.length,'Território duplicado');
  for(var t of e.territories) {
    var cadastro=territories.get(t.territory_id);
    assert.eq(t.territory_name,cadastro?.territory_name,'Território copiado incorretamente');
    assert.eq(t.region_id,cadastro?.region_id,'Região copiada incorretamente');
  }
}
for(var o of b.orders.find({}).toArray()) {
  assert(customers.has(o.customer_id)&&employees.has(String(o.employee_id))&&shippers.has(String(o.shipper_id)),'Referência de pedido inválida');
  assert(o.required_date>=o.order_date && (o.shipped_date===null || o.shipped_date>=o.order_date),'Datas do pedido inválidas');
  assert.eq(new Set(o.items.map(i=>String(i.product._id))).size,o.items.length,'Produto duplicado no pedido');
  for(var i of o.items) {
    var produto=products.get(String(i.product._id));
    assert.eq(i.product.name,produto?.product_name,'Nome de produto copiado incorretamente');
    assert.eq(i.product.category._id,produto?.category._id,'Categoria do item incorreta');
    assert.eq(i.product.category.name,produto?.category.name,'Nome de categoria do item incorreto');
  }
}
print('PASSOU: estruturas BSON, referências, cópias dos cadastros e coerência temporal.');
var total=b.orders.aggregate([{$unwind:'$items'},{$group:{_id:null,itens:{$sum:1},
  valor_exato:{$sum:{$multiply:['$items.unit_price','$items.quantity',{$subtract:[Decimal128('1'),'$items.discount']}]}}}}]).toArray();
print(EJSON.stringify({totais:total}));
// Sem hint: observa o plano escolhido pelo otimizador para a consulta real.
var plano=b.orders.find({customer_id:'VINET',order_date:{$gte:ISODate('1996-01-01'),$lt:ISODate('1997-01-01')}}).sort({order_date:1}).explain('executionStats');
print(EJSON.stringify({indice:plano.queryPlanner.winningPlan,retornados:plano.executionStats.nReturned,
  documentos_examinados:plano.executionStats.totalDocsExamined,chaves_examinadas:plano.executionStats.totalKeysExamined}));
for(var nome of ['orders','products']) print(EJSON.stringify({colecao:nome,indices:b.getCollection(nome).getIndexes()}));
print('Pedido de estudo:');
print(EJSON.stringify(b.orders.findOne({_id:10248}),null,2));
