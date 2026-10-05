// Teste isolado. Nunca escreve em northwind. Recusa reutilizar banco de teste.
load('/mongo/entrega02/01_modelo.js');
var teste=db.getSiblingDB('northwind_entrega02_teste_validadores');
assert.eq(teste.getCollectionNames().length,0,'Banco de teste já existe; inspecione-o antes de continuar.');
try {
  configurar(teste);
  var original=db.getSiblingDB('northwind').orders.findOne({_id:10248});
  assert(original,'Execute a carga primeiro');
  teste.orders.insertOne(original);
  var casos=[
    ['preço como texto',d=>d.items[0].unit_price='14.00'],
    ['quantidade zero',d=>d.items[0].quantity=Int32(0)],
    ['desconto de 100%',d=>d.items[0].discount=Decimal128('1')],
    ['data como texto',d=>d.order_date='1996-07-04'],
    ['endereço ausente',d=>delete d.shipping]
  ];
  for(var [nome,alterar] of casos) {
    var invalido=EJSON.parse(EJSON.stringify(original),{relaxed:false});
    alterar(invalido);
    var rejeitado=false;
    try {teste.orders.replaceOne({_id:original._id},invalido);} catch(erro) {
      if(erro.code!==121) throw erro;
      rejeitado=true;
    }
    assert(rejeitado,'Validador aceitou: '+nome);
    print('PASSOU: rejeitado '+nome+' (código 121).');
  }
  assert.eq(EJSON.stringify(teste.orders.findOne({_id:original._id})),EJSON.stringify(original),'Documento alterado após rejeição');
  print('PASSOU: documento original preservado após todas as rejeições.');
} finally {
  assert.commandWorked(teste.dropDatabase());
}
