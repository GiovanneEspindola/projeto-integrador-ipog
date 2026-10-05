var b = db.getSiblingDB('northwind');
// As três condições precisam ocorrer no MESMO elemento do array.
var mesmoItem = [
  {$match: {items: {$elemMatch: {
    'product._id': 11, quantity: {$gte: 10}, discount: {$gt: Decimal128('0')}
  }}}},
  {$project: {_id:1,items:{$filter:{input:'$items',as:'i',cond:{$and:[
    {$eq:['$$i.product._id',11]},{$gte:['$$i.quantity',10]},
    {$gt:['$$i.discount',Decimal128('0')]}
  ]}}}}},
  {$sort:{_id:1}}
];
// Contraste: as mesmas condições escritas separadamente podem ser atendidas por itens diferentes.
var independentes = {'items.product._id': 11, 'items.quantity': {$gte: 10},
  'items.discount': {$gt: Decimal128('0')}};
// Um documento de entrada continua sendo um documento de saída.
var pedido = [
  {$match:{_id:10248}},
  {$project:{_id:1,produtos:{$map:{input:'$items',as:'i',in:'$$i.product.name'}},
    valor:{$reduce:{input:'$items',initialValue:Decimal128('0'),in:{$add:[
      '$$value',{$multiply:['$$this.unit_price','$$this.quantity',
        {$subtract:[Decimal128('1'),'$$this.discount']}]}]}}}}}
];
// Facetas diferentes sobre os mesmos documentos de entrada.
var painel = [
  {$match:{order_date:{$gte:ISODate('1997-01-01'),$lt:ISODate('1998-01-01')}}},
  {$facet:{
    volume:[{$count:'pedidos'}],
    envio:[{$group:{_id:{$cond:[{$eq:['$shipped_date',null]},'sem data','com data']},
      pedidos:{$sum:1}}},{$sort:{_id:1}}],
    tamanho:[{$group:{_id:{$size:'$items'},pedidos:{$sum:1}}},{$sort:{_id:1}}]
  }}
];
print(EJSON.stringify({mesmo_item:b.orders.aggregate(mesmoItem).toArray(),
  condicoes_independentes:b.orders.countDocuments(independentes),
  pedido:b.orders.aggregate(pedido).toArray(),painel:b.orders.aggregate(painel).toArray()},null,2));
