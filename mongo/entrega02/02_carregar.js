// Uso: mongosh ... --file /mongo/entrega02/02_carregar.js
// O transporte fica em /mongo/entrega02/dados/documentos.ejson (ver guia).
load('/mongo/entrega02/01_modelo.js');
var fs = require('fs');
var pacote = EJSON.parse(fs.readFileSync('/mongo/entrega02/dados/documentos.ejson', 'utf8'), {relaxed: false});
assert.eq(pacote.format, 'northwind-semana4-v1', 'Formato inesperado');
assert.eq(Object.keys(pacote.collections).sort(), Object.keys(modelos).sort(), 'Coleções incompletas');
var destino = db.getSiblingDB('northwind');
// Antes de gravar, recusa IDs repetidos e remoções da origem. Esta carga insere
// e atualiza: exclusões exigem revisão explícita; não apaga dados silenciosamente.
for (var [nome, docs] of Object.entries(pacote.collections)) {
  assert(Array.isArray(docs) && docs.length > 0, 'Coleção vazia ou inválida: ' + nome);
  var ids = docs.map(d => EJSON.stringify(d._id));
  assert.eq(new Set(ids).size, docs.length, 'IDs duplicados: ' + nome);
  var extras = destino.getCollection(nome).countDocuments({_id: {$nin: docs.map(d => d._id)}});
  assert.eq(extras, 0, 'Há IDs no destino ausentes na origem; revisar exclusões em ' + nome);
}
configurar(destino);
for (var [nome, docs] of Object.entries(pacote.collections)) {
  // replaceOne substitui também os arrays e campos que mudaram. upsert cria
  // documentos novos; o _id estável impede duplicação ao repetir a carga.
  var resultado = destino.getCollection(nome).bulkWrite(docs.map(doc => ({replaceOne: {
    filter: {_id: doc._id}, replacement: doc, upsert: true
  }})), {ordered: true});
  print(EJSON.stringify({colecao: nome, documentos: destino.getCollection(nome).countDocuments({}),
    inseridos: resultado.upsertedCount, modificados: resultado.modifiedCount}));
}
// Standalone: não há atomicidade entre coleções. Se falhar, corrigir a causa,
// repetir o MESMO arquivo completo e executar a conferência antes de consultar.
print('Carga finalizada. Execute a conferência; esta mensagem sozinha não comprova equivalência.');
