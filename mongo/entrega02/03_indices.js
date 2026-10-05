var banco = db.getSiblingDB('northwind');
// Igualdade no cliente e depois intervalo/ordenação pela data.
banco.orders.createIndex({customer_id: 1, order_date: 1}, {name: 'cliente_data'});
// Multikey: cada produto do array pode localizar seu pedido.
banco.orders.createIndex({'items.product._id': 1}, {name: 'produto_no_pedido'});
// Filtro do catálogo por categoria; _id já tem índice único automático.
banco.products.createIndex({'category._id': 1}, {name: 'categoria_produto'});
print('Índices criados: cliente_data, produto_no_pedido, categoria_produto.');
